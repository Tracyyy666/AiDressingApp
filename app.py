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

@app.route('/get_advice', methods=['POST'])
def get_advice():
    try:
        # 获取前端发送的 FormData
        height = request.form.get('height')
        weight = request.form.get('weight')
        gender = request.form.get('gender', '女性')
        body_shape = request.form.get('body_shape')
        style = request.form.get('style')
        photo = request.files.get('photo')

        # 强化 Prompt：要求鞋子建议必须“全面”
        prompt = f"""
你是一位拥有顶级审美和10年经验的私人形象顾问。请务必使用【中文】回答。
[用户档案] 性别:{gender} | 身高:{height}cm | 体重:{weight}kg | 体型:{body_shape} | 核心风格:{style}

[指令]
1. 给出上装、下装及【全面】的鞋子建议。
2. 【鞋子建议要求】：必须包含鞋型（如尖头、方头）、鞋跟高度（如厚底、3-5cm中跟）、材质（如漆皮、麂皮）以及它如何与下装衔接以优化比例（如延长腿部线条）。
3. 严禁使用“高腰”、“显瘦”等万金油词汇。请结合性别【{gender}】给出具有质感的专业描述。
4. 返回 JSON 格式，字段值必须为纯字符串：
{{ 
  "top": "具体上装描述（包含面料与色彩）", 
  "bottom": "具体下装描述（包含剪裁细节）", 
  "shoes": "全面的鞋履建议（包含鞋型、跟高及搭配逻辑）",
  "analysis": "针对该身材、性别和风格的深度深度逻辑解析", 
  "style_tags": ["风格标签1", "标签2"] 
}}
"""
        api_key = os.getenv('ZHIPU_AI_API_KEY')
        client = ZhipuAI(api_key=api_key)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        advice = json.loads(response.choices[0].message.content)
        return jsonify({"success": True, "advice": advice})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)