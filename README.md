# Playlist Analyse Bot

Бот для анализа плейлистов и поиска концертов на основе исполнителей. Поддерживает точный поиск концертов и AI-рекомендации через Google Gemini API.

## Установка и настройка

### 1. Установите зависимости

Если у вас еще нет виртуального окружения:
```bash
python3 -m venv venv
source venv/bin/activate  # На macOS/Linux
# или
venv\Scripts\activate  # На Windows
```

Установите пакеты:
```bash
pip install -r requirements.txt
```

### 2. Настройте переменные окружения

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Yandex Music API Token (обязательно)
YANDEX_MUSIC_TOKEN=your_yandex_music_token_here

# Google Gemini API Key (для AI-рекомендаций)
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB settings (опционально, есть значения по умолчанию)
# MONGO_HOST=localhost
# MONGO_PORT=27017
# MONGO_USERNAME=admin
# MONGO_PASSWORD=password123
# MONGO_DB=afisha_db
```

**Как получить токены:**
- **Yandex Music Token**: Настройки аккаунта → Разработчикам → Создать токен
- **Gemini API Key**: https://makersuite.google.com/app/apikey

### 3. Запустите MongoDB (если используется Docker)

```bash
docker-compose up -d
```

### 4. Запустите бота

```bash
cd src
python main.py
```

Программа попросит:
1. Ввести ссылку на плейлист Яндекс.Музыки
2. Ввести название города (или нажать Enter для значения по умолчанию: orenburg)

## Как это работает

1. **Точный поиск**: Бот ищет концерты исполнителей, которые точно есть в вашем плейлисте
2. **AI-рекомендации**: Google Gemini анализирует музыкальные стили исполнителей и рекомендует похожие концерты, даже если исполнителя нет в базе

## Пример использования

```
https://music.yandex.ru/users/user_id/playlists/12345
Введи город:
moscow
```

Бот выведет:
- Концерты с точными совпадениями исполнителей
- AI-рекомендации на основе музыкального стиля


