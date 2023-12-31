import redis
import openai
import os
from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS

openai.api_base = os.getenv("API_BASE")
openai.api_key = os.getenv("API_KEY")

redis_url = os.getenv("REDIS_URL")
r = redis.from_url(redis_url)

app = Flask(__name__)
CORS(app)

def upload_paper_content(key,paper):
    try:
        if not r.get("qa:"+key+":paper.txt"):
            r.set("qa:"+key+":paper.txt",paper)
        return 'done'
    except:
        return 'error'

def qa(key,question):
    paper = r.get("qa:"+key+":paper.txt").decode()
    response = openai.ChatCompletion.create(
        model="moonshot-v1-128k",
        messages=[ 
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
        },
        {
            "role": "user", 
            "content": "请根据论文内容:%s，回答下列问题:%s" %(paper,question)
        }
        ],
        temperature=0.3,
        stream=True,
    )
    return response


@app.route('/', methods=['GET'])
def _index():
    return 'hello qa'


@app.route('/upload', methods=['POST'])
def _upload():
    key = request.json.get('key')
    paper = request.json.get('paper')
    print(key)
    response = upload_paper_content(key,paper)
    return Response(response, mimetype='text/plain')


@app.route('/qa', methods=['POST'])
def _qa():
    key = request.json.get('key')
    question = request.json.get('question')
    print(key,question)
    try:
        def event_stream():
            for line in qa(key,question):
                text = line.choices[0].delta.get('content', '')
                if len(text): 
                    yield text
        return Response(event_stream(), mimetype='text/event-stream')
    except:
        return Response('error', mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000), host='0.0.0.0')
