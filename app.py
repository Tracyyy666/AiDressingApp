import os
import json
import base64
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from zhipuai import ZhipuAI
import sqlite3
from datetime import datetime

load_dotenv()
app = Flask(__name__)

# ========== 数据库初始化 ==========
def init_db():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  height INTEGER,
                  weight INTEGER,
                  body_shape TEXT,
                  styles TEXT,
                  top TEXT,
                  bottom TEXT,
                  shoes TEXT,
                  reason TEXT,
                  season TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()
init_db()

# ========== 通用 AI 推荐函数（支持图片/无图片） ==========
def call_ai_recommendation(gender, height, weight, body_shape, styles, season, photo_base64=None):
    """如果 photo_base64 有值，使用 glm-4v 多模态；否则使用 glm-4-flash"""
    shape_map = {
        'pear': '梨型（肩窄臀宽）',
        'apple': '苹果型（腰腹丰满）',
        'hourglass': '沙漏型（胸臀丰满腰细）',
        'rectangle': '矩形（肩腰臀宽相近）',
        'inverted_triangle': '倒三角（肩宽胯窄）'
    }
    body_shape_cn = shape_map.get(body_shape, body_shape)
    styles_cn = ', '.join(styles)
    
    season_desc = {
        '春': '春季，气温回暖，适合薄外套、风衣、长袖衬衫、针织开衫，颜色可选浅绿、淡粉、米白等清新色系',
        '夏': '夏季，炎热，适合短袖、短裤、连衣裙、凉鞋、亚麻、棉麻材质，颜色可选亮色或清爽浅色',
        '秋': '秋季，凉爽，适合针织衫、卫衣、夹克、长裤、乐福鞋，颜色可选棕色、卡其色、酒红等暖色调',
        '冬': '冬季，寒冷，适合羽绒服、大衣、毛衣、加绒裤、靴子，颜色可选深色或驼色，注意保暖'
    }
    season_advice = season_desc.get(season, season_desc['夏'])
    
    text_prompt = f"""你是一位拥有10年经验的顶级私人形象顾问。请务必使用【中文】回答。
[用户档案] 性别:{gender} | 身高:{height}cm | 体重:{weight}kg | 体型:{body_shape_cn} | 核心风格:{styles_cn} | 当前季节:{season}（{season_advice}）

[核心指令]
1. 请提供包含上装、下装及【全面鞋履】的完整穿搭方案。
2. 鞋子建议需包含：具体鞋型、材质、跟高逻辑以及它如何与整体比例衔接。
3. 如果提供了照片，请深度分析用户的肤色调性（冷暖）和面部氛围，并在建议中体现色彩美学。
4. 严禁使用“高腰”、“显瘦”等万金油词汇，请描述具体的剪裁（如：复古斜纹分割线）。
5. **季节适配**：根据当前季节推荐合适的服装材质、厚度、颜色和款式。
6. **区分男女**：必须针对【{gender}】的特点推荐服饰。
7. **杜绝同质化**：严禁推荐“白T恤+牛仔裤”、“小黑裙”等泛泛组合。

[输出要求] 必须返回纯 JSON 格式，字段值严禁嵌套对象：
{{
  "top": "具体上装描述",
  "bottom": "具体下装描述",
  "shoes": "全面鞋履建议",
  "analysis": "针对该用户数据的深度搭配哲学说明（包含季节适应性）"
}}"""
    
    api_key = os.getenv('ZHIPU_AI_API_KEY') or os.getenv('ZHIPU_API_KEY')
    if not api_key:
        raise Exception("未配置 API Key")
    client = ZhipuAI(api_key=api_key)
    
    if photo_base64:
        # 多模态：使用 glm-4v
        content_list = [
            {"type": "text", "text": text_prompt},
            {"type": "image_url", "image_url": {"url": photo_base64}}
        ]
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[{"role": "user", "content": content_list}],
            response_format={"type": "json_object"}
        )
    else:
        # 纯文本：使用 glm-4-flash
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": text_prompt}],
            temperature=0.95,
            response_format={"type": "json_object"}
        )
    
    content = response.choices[0].message.content
    return json.loads(content)

# ========== 路由：首页 ==========
@app.route('/')
def index():
    return render_template('index.html')

# ========== 路由：获取穿搭建议（支持图片、季节、历史记录） ==========
@app.route('/get_advice', methods=['POST'])
def get_advice():
    try:
        # 获取表单数据
        height = request.form.get('height')
        weight = request.form.get('weight')
        gender = request.form.get('gender', '女性')
        body_shape = request.form.get('body_shape')
        style = request.form.get('style')
        season = request.form.get('season', '夏')
        photo = request.files.get('photo')
        
        # 参数校验
        if not height or not weight or not body_shape or not style:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        height = int(height)
        weight = float(weight)
        styles = [style] if style else []
        
        # 处理图片转 base64（如果有）
        photo_base64 = None
        if photo:
            img_data = base64.b64encode(photo.read()).decode('utf-8')
            # 智谱要求 data URL 格式
            photo_base64 = f"data:image/jpeg;base64,{img_data}"
        
        # 调用 AI 推荐
        outfit = call_ai_recommendation(gender, height, weight, body_shape, styles, season, photo_base64)
        
        # 构造返回数据（适配前端期望的 advice 结构）
        advice = {
            "top": outfit.get("top", ""),
            "bottom": outfit.get("bottom", ""),
            "shoes": outfit.get("shoes", ""),
            "analysis": outfit.get("analysis", "")
        }
        return jsonify({"success": True, "advice": advice})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== 路由：保存历史记录 ==========
@app.route('/save_history', methods=['POST'])
def save_history():
    data = request.get_json()
    user_id = data.get('user_id', 'default')
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''INSERT INTO history 
                 (user_id, height, weight, body_shape, styles, top, bottom, shoes, reason, season, timestamp)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (user_id, data['height'], data['weight'], data['bodyShape'],
               ','.join(data['styles']), data['top'], data['bottom'], data['shoes'],
               data['reason'], data.get('season', '未知'), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

# ========== 路由：获取历史记录 ==========
@app.route('/get_history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id', 'default')
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''SELECT height, weight, body_shape, styles, top, bottom, shoes, reason, season, timestamp
                 FROM history WHERE user_id=? ORDER BY timestamp DESC LIMIT 10''', (user_id,))
    rows = c.fetchall()
    conn.close()
    history = []
    for r in rows:
        history.append({
            "height": r[0],
            "weight": r[1],
            "bodyShape": r[2],
            "styles": r[3].split(','),
            "top": r[4],
            "bottom": r[5],
            "shoes": r[6],
            "reason": r[7],
            "season": r[8],
            "timestamp": r[9]
        })
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)