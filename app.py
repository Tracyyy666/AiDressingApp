from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'AI 穿搭助手正在建设中'

if __name__ == '__main__':
    app.run(port=5000)
