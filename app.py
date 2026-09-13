from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv
import os

from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv
import os
import json
import uuid

load_dotenv()

app = Flask(__name__)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

CHAT_FILE = "chats.json"


def load_chats():
    if not os.path.exists(CHAT_FILE):
        return {}

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_chats():
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)


chats = load_chats()


# ถ้ายังไม่มีห้อง ให้สร้างห้องแรก
if not chats:
    chat_id = str(uuid.uuid4())

    chats[chat_id] = {
        "title": "แชตใหม่",
        "messages": []
    }

    save_chats()


@app.route("/")
def home():
    return render_template("index.html")


# ส่งรายชื่อห้องแชต
@app.route("/chats", methods=["GET"])
def get_chats():
    result = []

    for chat_id, chat in chats.items():
        result.append({
            "id": chat_id,
            "title": chat["title"]
        })

    return jsonify(result)


# สร้างห้องใหม่
@app.route("/new-chat", methods=["POST"])
def new_chat():
    chat_id = str(uuid.uuid4())

    chats[chat_id] = {
        "title": "แชตใหม่",
        "messages": []
    }

    save_chats()

    return jsonify({
        "id": chat_id,
        "title": "แชตใหม่"
    })


# โหลดข้อความของห้อง
@app.route("/chat/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    if chat_id not in chats:
        return jsonify({"messages": []})

    return jsonify({
        "messages": chats[chat_id]["messages"]
    })


# ส่งข้อความ
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json

    chat_id = data.get("chat_id")
    message = data.get("message", "").strip()

    if not chat_id or chat_id not in chats:
        return jsonify({
            "reply": "ไม่พบห้องแชตครับ"
        }), 400

    if not message:
        return jsonify({
            "reply": "พิมพ์ข้อความมาก่อนนะครับ 😄"
        })

    current_chat = chats[chat_id]

    # บันทึกข้อความผู้ใช้
    current_chat["messages"].append({
        "role": "user",
        "text": message
    })

    # ตั้งชื่อห้องจากข้อความแรก
    if current_chat["title"] == "แชตใหม่":
        current_chat["title"] = message[:30]

    # สร้างประวัติสำหรับ Gemini
    conversation = ""

    for item in current_chat["messages"]:
        if item["role"] == "user":
            conversation += f"ผู้ใช้: {item['text']}\n"
        else:
            conversation += f"ChatGemini PT: {item['text']}\n"

    prompt = f"""
คุณคือ ChatGemini PT ผู้ช่วย AI ที่เป็นมิตร

นี่คือประวัติของห้องแชตนี้:

{conversation}

ใช้ประวัติด้านบนเพื่อเข้าใจบริบทของการสนทนา
ตอบข้อความล่าสุดของผู้ใช้
ตอบเป็นภาษาไทยเป็นหลัก

ข้อความล่าสุด:
{message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        reply = response.text

        # บันทึกคำตอบ AI
        current_chat["messages"].append({
            "role": "assistant",
            "text": reply
        })

        save_chats()

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        # ถ้าเกิด Error เอาข้อความล่าสุดออก
        if current_chat["messages"]:
            current_chat["messages"].pop()

        return jsonify({
            "reply": f"เกิดข้อผิดพลาด: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)