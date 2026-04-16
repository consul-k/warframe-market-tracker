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

### Установка базовых пакетов

```bash
apt install python3 python3-venv python3-pip nginx git -y
```

### 1. Клонирование репозитория

```bash
cd /var/www
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

```bash
nano /var/www/warframe-market-tracker/.env
```

```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_ALLOWED_HOSTS=your_server_ip,localhost,127.0.0.1
DEBUG=False
```

### 4. Миграции и статика, заполнение базы данных предметов
```bash
cd warframe_market_tracker
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py load_market_items
```

### 5. Тестовый запуск Gunicorn
```bash
gunicorn warframe_market_tracker.wsgi:application --bind 0.0.0.0:8000
```
Откройте http://IP:8000
Используется только для проверки, в production не применяется.

### 6. Настройка Gunicorn как systemd сервиса

```bash
nano /etc/systemd/system/gunicorn.service
```

```
[Unit]
Description=Gunicorn for Django project
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/warframe-market-tracker/warframe_market_tracker
Environment="PATH=/var/www/warframe-market-tracker/venv/bin"
ExecStart=/var/www/warframe-market-tracker/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    warframe_market_tracker.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reexec
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn
```

Для простоты в примерах используется root, однако в production рекомендуется использовать отдельного пользователя (например, www-data).

тестовая проверка:

```bash
systemctl status gunicorn
```

### 7. Настройка Nginx

```bash
nano /etc/nginx/sites-available/default
```

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name IP;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/warframe-market-tracker/warframe_market_tracker/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Проверка конфигурации перед перезапуском:
```bash
nginx -t
systemctl restart nginx
```

### 8. Фоновые сервисы

```bash
nano /etc/systemd/system/price_watcher.service
```

```
[Unit]
Description=Price Watcher Service
After=network.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
User=root
WorkingDirectory=/var/www/warframe-market-tracker/warframe_market_tracker
Environment="PATH=/var/www/warframe-market-tracker/venv/bin"
ExecStart=/var/www/warframe-market-tracker/venv/bin/python /var/www/warframe-market-tracker/warframe_market_tracker/price_watcher.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable price_watcher
systemctl start price_watcher
systemctl status price_watcher
```

### 9. Обновление данных (cron)

```bash
crontab -e
```

Добавить:
```bash
0 4 * * * bash -c ' \
systemctl stop price_watcher && \
cd /var/www/warframe-market-tracker/warframe_market_tracker && \
/var/www/warframe-market-tracker/venv/bin/python manage.py load_market_items && \
systemctl start price_watcher \
' >> /var/log/warframe_cron.log 2>&1
```
cron не поддерживает многострочные команды, поэтому используется bash -c

### Дополнительно (если используется UFW)

Если у вас включён firewall (UFW), необходимо открыть порт 80:

```bash
ufw allow 80
ufw allow OpenSSH
ufw enable
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
│   ├── warframe_market_tracker/   ← settings, wsgi
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