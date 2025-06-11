import requests

api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

api_key = "api_key"

headers = {
    "Authorization": f"Api-Key {api_key}",
    "Content-Type": "application/json"
}

while True:
    user_input = input("Введите текст для исправления (или 'exit' для выхода): ").strip()
    if user_input.lower() == 'exit':
        print("Завершение работы.")
        break
    if not user_input:
        print("Пустой ввод. Пожалуйста, введите текст.")
        continue

    data = {
        "modelUri": "gpt://b1g9tvaaosk9fb1gnp8u/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0,
            "maxTokens": 200
        },
        "messages": [
            {
                "role": "system",
                "text": "Исправь грамматические, орфографические и пунктуационные ошибки в тексте. Сохраняй исходный порядок слов."
            },
            {
                "role": "user",
                "text": user_input
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        corrected_text = result.get("result", {}).get("alternatives", [])[0].get("message", {}).get("text", "")
        print("\nИсправленный текст:\n", corrected_text, "\n")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
    except (KeyError, IndexError):
        print("Ошибка при обработке ответа от API.")