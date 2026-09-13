from flask import Flask, request, jsonify, render_template, make_response
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
            data = json.load(f)

        # ล้างข้อมูลรูปแบบเก่าที่ใช้ร่วมกัน
        if data:
            first = next(iter(data.values()))

            if isinstance(first, dict) and "messages" in first:
                return {}

        return data

    except:
        return {}


def save_chats(chats):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)


def get_user_id():
    return request.cookies.get("user_id")


def create_user_id():
    return str(uuid.uuid4())


def get_user_chats(user_id):
    chats = load_chats()

    if user_id not in chats:
        chats[user_id] = {}

        chat_id = str(uuid.uuid4())

        chats[user_id][chat_id] = {
            "title": "แชตใหม่",
            "messages": []
        }

        save_chats(chats)

    return chats


@app.route("/")
def home():
    user_id = get_user_id()

    if not user_id:
        user_id = create_user_id()

    response = make_response(
        render_template("index.html")
    )

    response.set_cookie(
        "user_id",
        user_id,
        max_age=60 * 60 * 24 * 365
    )

    return response


@app.route("/chats")
def get_chats():
    user_id = get_user_id()

    if not user_id:
        user_id = create_user_id()

    chats = get_user_chats(user_id)

    result = []

    for chat_id, chat in chats[user_id].items():
        result.append({
            "id": chat_id,
            "title": chat["title"]
        })

    response = make_response(jsonify(result))

    response.set_cookie(
        "user_id",
        user_id,
        max_age=60 * 60 * 24 * 365
    )

    return response


@app.route("/new-chat", methods=["POST"])
def new_chat():
    user_id = get_user_id()

    if not user_id:
        user_id = create_user_id()

    chats = get_user_chats(user_id)

    chat_id = str(uuid.uuid4())

    chats[user_id][chat_id] = {
        "title": "แชตใหม่",
        "messages": []
    }

    save_chats(chats)

    response = make_response(jsonify({
        "id": chat_id,
        "title": "แชตใหม่"
    }))

    response.set_cookie(
        "user_id",
        user_id,
        max_age=60 * 60 * 24 * 365
    )

    return response


@app.route("/chat/<chat_id>")
def get_chat(chat_id):
    user_id = get_user_id()

    if not user_id:
        return jsonify({"messages": []})

    chats = get_user_chats(user_id)

    if chat_id not in chats[user_id]:
        return jsonify({"messages": []})

    return jsonify({
        "messages": chats[user_id][chat_id]["messages"]
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    user_id = get_user_id()

    if not user_id:
        user_id = create_user_id()

    chats = get_user_chats(user_id)

    chat_id = data.get("chat_id")
    message = data.get("message", "").strip()

if not chat_id or chat_id not in chats[user_id]:
    chat_id = str(uuid.uuid4())

    chats[user_id][chat_id] = {
        "title": "แชตใหม่",
        "messages": []
    }

    save_chats(chats)

    if not message:
        return jsonify({
            "reply": "พิมพ์ข้อความมาก่อนนะครับ 😄"
        })

    current_chat = chats[user_id][chat_id]

    current_chat["messages"].append({
        "role": "user",
        "text": message
    })

    if current_chat["title"] == "แชตใหม่":
        current_chat["title"] = message[:30]

    conversation = ""

    for item in current_chat["messages"]:
        if item["role"] == "user":
            conversation += f"ผู้ใช้: {item['text']}\n"
        else:
            conversation += f"ChatGemini PT: {item['text']}\n"

    prompt = f"""
คุณคือ ChatGemini PT ผู้ช่วย AI ที่เป็นมิตร

ประวัติการสนทนา:
{conversation}

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

        current_chat["messages"].append({
            "role": "assistant",
            "text": reply
        })

        save_chats(chats)

        result = jsonify({
            "reply": reply
        })

        result.set_cookie(
            "user_id",
            user_id,
            max_age=60 * 60 * 24 * 365
        )

        return result

    except Exception as e:

        if current_chat["messages"]:
            current_chat["messages"].pop()

        return jsonify({
            "reply": f"เกิดข้อผิดพลาด: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=False)