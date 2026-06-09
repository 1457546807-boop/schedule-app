import os
import base64
import json
import httpx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "服务器未配置 API Key"}), 500

    if "image" not in request.files:
        return jsonify({"error": "未收到图片"}), 400

    file = request.files["image"]
    img_bytes = file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    media_type = file.content_type or "image/jpeg"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": """请仔细分析这张课表图片，识别出每天每节课的安排。

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
- 值是数组，包含该天"有课"的节次编号（1-12）
- 节次定义：1-2节早上第一二节，3-4节第三四节，5节午后第一节，6-7节下午，8-9节下午后段，10-12节晚上
- 如果图片中某天某节有课程内容（非空白），就把那个节次加入数组
- 合并课（如跨3-4节）请把两节都加入
- 只返回JSON，不要解释""",
                    },
                ],
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    try:
        resp = httpx.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = "".join(c.get("text", "") for c in data.get("content", []))

        # 提取 JSON
        import re
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
