# Импорт модулей
import requests
#import os
#from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from moviepy import VideoFileClip, ImageClip, ColorClip, CompositeVideoClip

# Настройки
PIXABAY_API_KEY = ('PIXABAY_API_KEY')  # Замените на ваш API ключ

search_query = 'Pepsi Cola'  # Ваш поисковый запрос
per_page = 3  # Количество видео для загрузки

logo_path = 'logo.png'  # Путь к вашему логотипу

def download_pixabay_videos(query, per_page=3):
    url = 'https://pixabay.com/api/videos/'

    params = {
        'key': PIXABAY_API_KEY,
        'q': query,
        'per_page': per_page,
        'safesearch': 'true'
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        videos = response.json()['hits']
        video_paths = []
        for idx, video in enumerate(videos):
            # Выбираем видео с наилучшим качеством
            video_files = video['videos']
            if 'large' in video_files:
                video_url = video_files['large']['url']
            elif 'medium' in video_files:
                video_url = video_files['medium']['url']
            else:
                video_url = video_files['small']['url']

            video_response = requests.get(video_url)
            video_filename = f'video_{idx}.mp4'
            with open(video_filename, 'wb') as f:
                f.write(video_response.content)
            video_paths.append(video_filename)
        return video_paths
    else:
        print('Ошибка при запросе к Pixabay API:', response.status_code)
        print('Сообщение об ошибке:', response.text)
        return []


def overlay_logo_on_video(video_path, logo_path, output_path):
    # Загрузка видео
    video_clip = VideoFileClip(video_path)

    # Загрузка логотипа
    logo = ImageClip(logo_path).with_duration(video_clip.duration)

    # Изменение размера логотипа
    logo = logo.resized(height=132)

    # Получение размеров логотипа
    logo_width, logo_height = logo.size

    # Определение отступов
    margin_right = 8
    margin_top = 8

    # Создание фона с отступами
    background = ColorClip(size=(logo_width + margin_right, logo_height + margin_top), color=(0, 0, 0))
    background = background.with_duration(video_clip.duration).with_opacity(0)

    # Размещение логотипа на фоне
    logo = logo.with_position((margin_right, margin_top))
    logo_with_margin = CompositeVideoClip([background, logo])

    # Размещение логотипа с отступами на видео
    logo_with_margin = logo_with_margin.with_position(("right", "top"))
    final_video = CompositeVideoClip([video_clip, logo_with_margin])

    # Сохранение итогового видео
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')

    # Освобождение ресурсов
    video_clip.close()
    final_video.close()

# Основной процесс

video_paths = download_pixabay_videos(search_query, per_page)

if video_paths:
    for video_path in video_paths:
        output_path = f'logo_{video_path}'
        overlay_logo_on_video(video_path, logo_path, output_path)
        print(f'Видео с наложенным логотипом сохранено: {output_path}')
else:
    print('Не удалось скачать видео.')

# Импорт модулей
from moviepy import VideoFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips

# Пути к итоговым видео с логотипами
video_paths = ['logo_video_0.mp4', 'logo_video_1.mp4', 'logo_video_2.mp4']
output_path = 'merged_video.mp4'

# Загружаем и приводим к одному размеру (по желанию)
target_size = (640, 360)
video_clips = [VideoFileClip(path).resized(target_size) for path in video_paths]

# Склеиваем видео последовательно
final_clip = concatenate_videoclips(video_clips, method='compose')

# Сохраняем результат
final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

# Освобождение ресурсов
for clip in video_clips:
    clip.close()
final_clip.close()

print(f'Итоговое видео сохранено как {output_path}')