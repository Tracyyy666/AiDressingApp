import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from zhipuai import ZhipuAI

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    height = data.get('height')
    weight = data.get('weight')
    body_shape = data.get('bodyShape')
    styles = data.get('styles', [])
    
    shape_map = {
        'pear': '梨型（肩窄臀宽）',
        'apple': '苹果型（腰腹丰满）',
        'hourglass': '沙漏型（胸臀丰满腰细）',
        'rectangle': '矩形（肩腰臀宽相近）',
        'inverted_triangle': '倒三角（肩宽胯窄）'
    }
    body_shape_cn = shape_map.get(body_shape, body_shape)
    styles_cn = ', '.join(styles)

    prompt = f"""
你是一位专业形象顾问。用户身高{height}cm，体重{weight}kg，体型为{body_shape_cn}，喜欢的风格是{styles_cn}。
请推荐一套完整的穿搭，包含上衣、下装、鞋子，并给出推荐理由（需结合体型和风格）。
请严格按以下JSON格式输出，不要有其他文字：
{{"top": "上衣名称", "bottom": "下装名称", "shoes": "鞋子名称", "reason": "推荐理由"}}
"""
    api_key = os.getenv('ZHIPU_API_KEY')
    if not api_key:
        return jsonify({"error": "服务器未配置 API Key，请在 .env 文件中设置 ZHIPU_API_KEY"}), 500

    try:
        client = ZhipuAI(api_key=api_key)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        outfit = json.loads(content)
        return jsonify(outfit)
    except Exception as e:
        return jsonify({"error": f"AI 调用失败: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)