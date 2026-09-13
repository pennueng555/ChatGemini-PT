@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    user_id = get_user_id()

    if not user_id:
        user_id = create_user_id()

    chats = get_user_chats(user_id)

    chat_id = data.get("chat_id")
    message = data.get("message", "").strip()

    # ถ้าไม่มีห้องแชต ให้สร้างใหม่
    if not chat_id or chat_id not in chats[user_id]:
        chat_id = str(uuid.uuid4())

        chats[user_id][chat_id] = {
            "title": "แชตใหม่",
            "messages": []
        }

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