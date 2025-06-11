from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import gspread
from openai import OpenAI
from oauth2client.service_account import ServiceAccountCredentials
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY

app = Flask(__name__)
CORS(app)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-creds.json", scope)
gclient = gspread.authorize(creds)
sheet = gclient.open("Записи в салон").sheet1

# Assistant ID
ASSISTANT_ID = "ASSISTANT_ID"

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204  # Preflight OK

    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"error": "Пустое сообщение"}), 400

    try:
        # Создаём диалог
        thread = client.beta.threads.create()

        # Добавляем сообщение пользователя
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_msg
        )

        # Запускаем ассистента
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Ждём завершения
        while run.status not in ["completed", "failed", "cancelled"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status != "completed":
            return jsonify({"error": f"Ассистент не завершил работу: {run.status}"}), 500

        # Получаем ответ ассистента
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value

        # Проверка на триггер для записи
        triggers = ["запись оформлена", "вы записаны", "ваша запись подтверждена"]
        if any(t in reply.lower() for t in triggers):
            # Telegram
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": f"📅 Новая запись: {user_msg}"
                }
            )
            # Google Sheets
            sheet.append_row([user_msg])

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
