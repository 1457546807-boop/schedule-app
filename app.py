import os
import base64
import json
import re
import httpx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_API_URL = os.environ.get("CLAUDE_API_URL", "https://vip.aipro.love/v1")

PROMPT = """请仔细分析这张课表图片，识别出每天每节课的安排。

请以严格的JSON格式返回，不要有任何其他文字：
{
  "week_label": "课表上显示的周次或日期范围（如没有则留空字符串）",
  "schedule": {
    "周一": [1,2,3],
    "周二": [],
    "周三": [1,2,5,6],
    "周四": [3,4],
    "周五": [1,2],
    "周六": [],
    "周日": []
  }
}

说明：
- schedule中每个key是星期几（周一到周日）
- 值是数组，包含该天有课的节次编号（1-12）
- 注意：课表第一列可能是周日，请仔细看列标题（日、一、二、三...）来判断，不要自己假设顺序
- 判断有课的标准：格子里有彩色背景+文字内容就是有课，纯白色/空白格子就是空余
- 合并课（如跨3-4节）请把两节都加入
- 只返回JSON，不要解释"""

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if not CLAUDE_API_KEY:
        return jsonify({"error": "服务器未配置 API Key"}), 500

    if "image" not in request.files:
        return jsonify({"error": "未收到图片"}), 400

    file = request.files["image"]
    img_bytes = file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    media_type = file.content_type or "image/jpeg"

    # OpenAI 兼容格式
    payload = {
        "model": "claude-opus-4-7",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{img_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": PROMPT
                    }
                ]
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLAUDE_API_KEY}",
    }

    api_url = CLAUDE_API_URL.rstrip("/") + "/chat/completions"

    try:
        resp = httpx.post(api_url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]

        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return jsonify({"error": "AI 返回格式异常，请重试"}), 500
        result = json.loads(m.group())
        return jsonify(result)

    except httpx.HTTPStatusError as e:
        msg = e.response.text[:200]
        return jsonify({"error": f"API 请求失败: {msg}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
