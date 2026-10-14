# LinguaTrack

MVP веб-приложения для изучения иностранных слов: личные аккаунты, карточки, интервальное повторение SM-2, статистика, озвучка средствами браузера и Telegram webhook.

## Возможности

- Регистрация и вход; карточки изолированы по владельцу.
- Словарь с поиском, фильтрами, редактированием и удалением.
- Поля карточки: слово, перевод, язык, пример, заметка, уровень.
- Тренировка с оценкой воспоминания и автоматическим расписанием повторений.
- Статистика словаря, выученных слов, точности и активности за неделю.
- Озвучивание карточек через Speech Synthesis API браузера.
- Telegram-команды: /today, /test, /progress, /say слово и /cards. Поддерживаются привязка аккаунта одноразовой ссылкой и голосовые сообщения через gTTS.

## Запуск локально

Требуется Python 3.10 или новее. Выполните в PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver

Откройте http://127.0.0.1:8000/ и создайте аккаунт. SQLite-база появится в db.sqlite3.

## Подключение Telegram

Создайте бота у @BotFather. Заполните TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME и длинный случайный TELEGRAM_WEBHOOK_SECRET в окружении. Разверните сайт на HTTPS и установите webhook:

$secret = $env:TELEGRAM_WEBHOOK_SECRET
$token = $env:TELEGRAM_BOT_TOKEN
$body = @{ url = 'https://ваш-домен/telegram/webhook/'; secret_token = $secret } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://api.telegram.org/bot$token/setWebhook" -ContentType 'application/json' -Body $body

Затем войдите в приложение, откройте «Мой прогресс» и нажмите «Подключить бота». Ссылка привяжет Telegram ID к текущему аккаунту. Для локального сайта понадобится публичный HTTPS-туннель, чтобы Telegram мог обращаться к webhook.

Команда /say использует gTTS; серверу нужен исходящий доступ в интернет. В браузере карточки озвучиваются системными голосами устройства.

Для production настройте HTTPS, задайте случайный DJANGO_SECRET_KEY и DJANGO_ALLOWED_HOSTS, установите DJANGO_DEBUG=False, храните секреты в защищённом хранилище и регулярно создавайте резервные копии SQLite.
