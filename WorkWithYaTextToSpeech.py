import json
import requests
import jwt  # PyJWT
import time

# Путь к вашему JSON-файлу ключа сервисного аккаунта
SERVICE_ACCOUNT_KEY_FILE = "./auth/authorized_key.json"

# Загрузка JSON-файла
with open(SERVICE_ACCOUNT_KEY_FILE, 'r') as f:
    key_data = json.load(f)

# Извлечение данных из JSON
service_account_id = key_data.get('service_account_id')
private_key = key_data.get('private_key')
key_id = key_data.get('id')  # Используем 'id' как 'kid'

# Проверка наличия необходимых полей
if not all([service_account_id, private_key, key_id]):
    raise ValueError("JSON-файл ключа сервисного аккаунта не содержит необходимых полей.")

# Текущее время и время истечения токена
now = int(time.time())
expire = now + 3600  # Токен будет действителен 1 час

# Заголовок JWT
headers = {
    'alg': 'PS256',
    'typ': 'JWT',
    'kid': key_id  # Убедитесь, что 'kid' соответствует ожидаемому значению
}

# Полезная нагрузка JWT
payload = {
    'iss': service_account_id,
    'sub': service_account_id,
    'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
    'iat': now,
    'exp': expire
}

# Генерация JWT-токена
jwt_token = jwt.encode(payload, private_key, algorithm='PS256', headers=headers)

# Отправка запроса для получения IAM токена
url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
response = requests.post(url, json={'jwt': jwt_token})

# Обработка ответа
if response.status_code == 200:
    iam_token = response.json().get('iamToken')
    print("IAM токен получен:", iam_token)
else:
    print("Ошибка при получении IAM токена:", response.status_code, response.text)

from speechkit import Session, SpeechSynthesis
import pyaudio

# Замените на ваш IAM-токен и идентификатор каталога
api_key = 'api_key'
folder_id = 'folder_id'


# Создание сессии
session = Session.from_api_key(api_key, folder_id)

# Инициализация синтеза речи
synthesizer = SpeechSynthesis(session)

# Текст для синтеза
text = 'Шла Маша по шоссе и сосала сушку!'

# Синтез речи и получение аудиоданных
audio_data = synthesizer.synthesize_stream(
    text=text,
    voice='oksana',
    format='lpcm',
    sampleRateHertz=16000
)

# Воспроизведение аудио с использованием PyAudio
def play_audio(audio_bytes, sample_rate=16000):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True)
    stream.write(audio_bytes)
    stream.stop_stream()
    stream.close()
    p.terminate()

play_audio(audio_data)
from gtts import gTTS
try:
    # Создаём объект gTTS
    tts = gTTS(text=text, lang='ru')

    # Временное имя файла
    filename = "output2.mp3"

    # Сохраняем аудио в файл
    tts.save(filename)
except Exception as e:
    print(f"Произошла ошибка: {e}")

from gtts import gTTS
from playsound import playsound
import os

def text_to_speech(text, lang='ru'):
    """
    Преобразует текст в аудио и воспроизводит его.
    :param text: Текст для синтеза речи.
    :param lang: Код языка (по умолчанию 'ru' для русского).
    """
    try:
        # Создаём объект gTTS
        tts = gTTS(text=text, lang=lang)

        # Временное имя файла
        filename = "output.mp3"

        # Сохраняем аудио в файл
        tts.save(filename)
        print("Аудиофайл сохранён как 'output.mp3'")

        # Воспроизводим аудиофайл
        playsound(filename)

        # Удаляем файл после воспроизведения (опционально)
        #os.remove(filename)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    user_text = input("Введите текст для озвучивания: ")
    if user_text.strip() == "":
        print("Пустой текст не может быть озвучен.")
    else:
        text_to_speech(user_text)