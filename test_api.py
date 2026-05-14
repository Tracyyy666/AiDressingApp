import requests
import json

print("开始测试后端接口...")

url = "http://127.0.0.1:5000/recommend"
data = {
    "height": 170,
    "weight": 65,
    "bodyShape": "hourglass",
    "styles": ["休闲"]
}

print(f"请求地址: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"HTTP状态码: {response.status_code}")
    print("返回内容:", response.text)  # 先打印原始文本
    if response.status_code == 200:
        result = response.json()
        print("解析后的JSON:", result)
    else:
        print("请求失败，状态码不是200")
except requests.exceptions.ConnectionError:
    print("连接失败：请确认 Flask 是否正在运行 (python app.py)")
except Exception as e:
    print(f"其他错误: {type(e).__name__}: {e}")