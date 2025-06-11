import requests
import base64
import uuid

import truststore
truststore.inject_into_ssl()

# Замените на ваши реальные client_id и client_secret
client_id = ('client_id')
client_secret = 'client_secret'

# Функция для получения токена доступа
def get_access_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {encoded_credentials}'
    }

    data = {
        'scope': 'GIGACHAT_API_PERS'
    }

    auth_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'

    response = requests.post(auth_url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Ошибка при получении токена: {response.status_code} - {response.text}")
        return None

# Функция для отправки запроса к GigaChat API
def send_gigachat_request(access_token, user_input):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'GigaChat:lite',
        'messages': [
            {'role': 'user', 'content': user_input}
        ]
    }

    api_url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'

    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        reply = response.json()
        return reply['choices'][0]['message']['content']
    else:
        print(f"Ошибка при обращении к GigaChat API: {response.status_code} - {response.text}")
        return None

def main():
    access_token = get_access_token(client_id, client_secret)
    if not access_token:
        return

    print("Введите ваш запрос (для выхода введите 'exit'):")
    while True:
        user_input = input(">> ")
        if user_input.lower() == 'exit':
            print("Завершение работы.")
            break
        response = send_gigachat_request(access_token, user_input)
        if response:
            print(f"GigaChat: {response}")

if __name__ == "__main__":
    main()