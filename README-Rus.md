# Warframe Market Tracker

Веб-приложение для отслеживания цен на предметы на Warframe Market и определения оптимального момента для продажи.

## Описание

Проект помогает игрокам отслеживать цены на внутриигровые предметы и понимать, когда выгодно их продавать.

Пользователь задаёт желаемую цену продажи. Приложение регулярно обновляет рыночные данные и сравнивает их с заданной ценой.

Когда рыночная цена достигает нужного уровня, пользователь получает уведомление.

## Как это работает

- Пользователь выбирает предмет (с автодополнением)
- Указывает желаемую цену продажи
- Фоновый процесс регулярно получает данные с рынка
- Система анализирует:
  - минимальную цену
  - среднюю цену за последние 48 часов
- Если заданная цена становится **меньше или равна минимальной цене на рынке**, срабатывает уведомление

## Возможности

- Поиск предметов с автодополнением
- Отслеживание нескольких предметов
- Фоновый мониторинг цен
- Автоматические уведомления
- Поддержка предметов с рангами (моды)
- Ежедневное обновление базы данных
- Простой интерфейс

## Технологии

- Backend: Django
- Frontend: HTML, CSS, JavaScript
- База данных: SQLite
- WSGI-сервер: Gunicorn
- Reverse proxy: Nginx
- Фоновые задачи: systemd
- Планировщик: cron

## Архитектура

```
Клиент (браузер)
    ↓
Nginx
    ↓
Gunicorn
    ↓
Django
    ↓
SQLite

Фоновые процессы:
- price_watcher (systemd)
- cron (ежедневные обновления)
```

## Развёртывание (VPS)

### 1. Клонирование репозитория

```bash
git clone https://github.com/consul-k/warframe-market-tracker
cd warframe-market-tracker
```

### 2. Виртуальное окружение
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Переменные окружения

Создайте файл .env:
```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_ALLOWED_HOSTS=your_server_ip,localhost,127.0.0.1
DEBUG=False
```
### 4. Миграции и статика
```bash
cd warframe_market_tracker
python manage.py migrate
python manage.py collectstatic --noinput
```
### 5. Запуск Gunicorn
```bash
gunicorn warframe_market_tracker.wsgi:application --bind 127.0.0.1:8000
```
### 6. Настройка Nginx

```nginx
server {
    listen 80;
    server_name your_server_ip;

    location /static/ {
        alias /var/www/warframe-market-tracker/warframe_market_tracker/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```
### 7. Фоновые сервисы

```bash
systemctl enable price_watcher
systemctl start price_watcher
```
### 8. Обновление данных (cron)

```bash
0 4 * * * /usr/bin/systemctl stop price_watcher && \
cd /var/www/warframe-market-tracker/warframe_market_tracker && \
/var/www/warframe-market-tracker/venv/bin/python manage.py load_market_items && \
/usr/bin/systemctl start price_watcher >> /var/log/warframe_cron.log 2>&1
```
## Ограничения

- SQLite может блокировать базу при одновременной записи
- Это решено временной остановкой фонового процесса при обновлении данных

## Использование
- Открыть сайт в браузере
- Создать аккаунт
- Добавить предметы для отслеживания
- Указать желаемую цену
- Дождаться уведомления


## Структура проекта

```
warframe-market-tracker/
├── warframe_market_tracker/
│   ├── tracker/
│   ├── staticfiles/
│   ├── manage.py
│   └── ...
├── nginx/
├── requirements.txt
├── gunicorn_config.py
└── README.md
```

## Локальный запуск

```bash
git clone https://github.com/consul-k/warframe-market-tracker
cd warframe-market-tracker

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd warframe_market_tracker
python manage.py migrate
python manage.py runserver
```

Открыть:
http://127.0.0.1:8000

## Итог

Проект демонстрирует:

- Разработку веб-приложения на Django
- Развёртывание на VPS без Docker
- Настройку Nginx и Gunicorn
- Работу с фоновыми процессами (systemd)
- Планирование задач (cron)
- Решение реальных проблем (например, блокировка SQLite)

## Цель проекта

- Решение практической задачи для игроков Warframe
- Практика backend-разработки
- Получение опыта деплоя и настройки сервера
- Понимание работы фоновых задач