from xml.etree.ElementInclude import include

import requests
from config import API_KEY  # ← импорт ключа из модуля

# Список голосов, поддерживающих русский язык
voices = {
    "1": {
        "name": "Русский женский (Анна)",
        "id": "064b17af-d36b-4bfb-b003-be07dba1b649"
    },
    "2": {
        "name": "Русский мужской (Иван)",
        "id": "2b3bb17d-26b9-421f-b8ca-1dd92332279f"
    }
}

def choose_voice():
    print("Выберите русский голос:")
    for key, voice in voices.items():
        print(f"{key}: {voice['name']}")

    choice = input("Введите номер голоса: ").strip()
    return voices.get(choice, voices["1"])  # по умолчанию — первый голос

def main():
    url = "https://api.cartesia.ai/tts/bytes"
    headers = {
        "Cartesia-Version": "2024-06-10",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    transcript = input("Введите текст на русском языке: ").strip()
    selected_voice = choose_voice()

    payload = {
        "model_id": "sonic-2",
        "transcript": transcript,
        "voice": {
            "mode": "id",
            "id": selected_voice["id"]
        },
        "output_format": {
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100
        },
        "language": "ru"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        with open("../tts/output.wav", "wb") as f:
            f.write(response.content)
        print("✅ Аудио успешно сохранено в файл output.wav")
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
