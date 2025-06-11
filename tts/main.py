import logging
import requests
import tempfile
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from config import API_KEY, BOT_TOKEN
from voice import voices

# Логирование
logging.basicConfig(level=logging.INFO)

# Состояния
CHOOSING_VOICE, TYPING_TEXT = range(2)

# Сохраняем выбранный голос
user_voice_choice = {}

# Клавиатура с голосами
voice_keyboard = [[v['name']] for v in voices.values()]
markup = ReplyKeyboardMarkup(voice_keyboard, one_time_keyboard=True, resize_keyboard=True)

def save_response_as_wav(raw_bytes: bytes) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with open(tmp_file.name, "wb") as f:
        f.write(raw_bytes)
    return tmp_file.name

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери голос для озучивания текста:", reply_markup=markup)
    return CHOOSING_VOICE

async def choose_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_name = update.message.text
    for v in voices.values():
        if v["name"] == selected_name:
            user_voice_choice[update.effective_user.id] = v["id"]
            break
    else:
        await update.message.reply_text("\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0432\u044b\u0431\u043e\u0440. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0441\u043d\u043e\u0432\u0430.", reply_markup=markup)
        return CHOOSING_VOICE

    await update.message.reply_text("\u0422\u0435\u043f\u0435\u0440\u044c \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043a\u0441\u0442, \u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u043d\u0443\u0436\u043d\u043e \u043e\u0437\u0443\u0447\u0438\u0442\u044c:")
    return TYPING_TEXT

async def synthesize_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transcript = update.message.text
    voice_id = user_voice_choice.get(user_id)

    if not voice_id:
        await update.message.reply_text("\u0413\u043e\u043b\u043eс \u043d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d. \u041d\u0430\u0447\u043d\u0438\u0442\u0435 \u0441 /start.")
        return ConversationHandler.END

    headers = {
        "Cartesia-Version": "2024-06-10",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model_id": "sonic-2",
        "transcript": transcript,
        "voice": {
            "mode": "id",
            "id": voice_id
        },
        "output_format": {
            "container": "wav",
            "encoding": "pcm_s16le",
            "sample_rate": 44100
        },
        "language": "ru"
    }

    await update.message.reply_text("\u26f3\ufe0f \u0413\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f аудио...")

    response = requests.post("https://api.cartesia.ai/tts/bytes", headers=headers, json=payload)

    if response.status_code == 200 and len(response.content) > 1000:
        try:
            wav_path = save_response_as_wav(response.content)
            with open(wav_path, "rb") as audio_file:
                await update.message.reply_audio(audio=InputFile(audio_file, filename="speech.wav"))
        except Exception as e:
            await update.message.reply_text(f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 при обработке WAV: {str(e)}")
    else:
        await update.message.reply_text(f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 API: {response.status_code} - {response.text}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\u041e\u043f\u0435\u0440\u0430\u0446\u0438\u044f \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.")
    return ConversationHandler.END

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_VOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_voice)],
            TYPING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, synthesize_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
