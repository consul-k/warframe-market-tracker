# Warframe Market Tracker

A web application for tracking item prices on Warframe Market and identifying optimal selling opportunities.

## Overview

This project helps players monitor market prices for in-game items and determine the best time to sell them.

The user specifies a desired selling price. The application continuously tracks market data and compares it with the user's target.

When the market price reaches the desired level, the user is notified.

## How It Works

- The user selects an item (with autocomplete support)
- The user sets a target selling price
- A background worker periodically fetches market data
- The system analyzes:
  - Minimum market price
  - Average price over the last 48 hours
- If the target price becomes **greater than or equal to the current minimum price**, a notification is triggered

## Features

- Autocomplete item search
- Tracking multiple items per user
- Background price monitoring
- Automatic notifications
- Support for ranked items (mods)
- Daily database updates
- Minimal UI

## Tech Stack

- Backend: Django
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Web server: Gunicorn
- Reverse proxy: Nginx
- Background tasks: systemd
- Scheduler: cron

## Architecture

```
Client (Browser)
    ↓
Nginx
    ↓
Gunicorn
    ↓
Django
    ↓
SQLite

Background:
- price_watcher (systemd)
- cron (daily updates)
```

## Deployment (VPS)

### Install base packages

```bash
apt install python3 python3-venv python3-pip nginx git -y
```

### 1. Clone repository

```bash
cd /var/www
git clone https://github.com/consul-k/warframe-market-tracker
cd warframe-market-tracker
```

### 2. Setup virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create .env file:

```bash
nano /var/www/warframe-market-tracker/.env
```

```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_ALLOWED_HOSTS=your_server_ip,localhost,127.0.0.1
DEBUG=False
```

### 4. Migrations, static files and initial data
```bash
cd warframe_market_tracker
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py load_market_items
```

### 5. Test run (Gunicorn)

```bash
gunicorn warframe_market_tracker.wsgi:application --bind 0.0.0.0:8000
```
Open http://IP:8000

Used only for testing. In production, Gunicorn runs via systemd.

### 6. Configure Gunicorn as systemd service

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

For simplicity, root is used in this example. In production, it is recommended to use a dedicated user (e.g. www-data).

Check status:

```bash
systemctl status gunicorn
```

### 7. Configure Nginx

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
Static files are served directly by Nginx (from the staticfiles directory created by collectstatic).

Test and restart:

```bash
nginx -t
systemctl restart nginx
```

### 8. Background services

```bash
nano /etc/systemd/system/price_watcher.service
```

```
[Unit]
Description=Price Watcher Service
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/warframe-market-tracker/warframe_market_tracker
Environment="PATH=/var/www/warframe-market-tracker/venv/bin"
ExecStart=/var/www/warframe-market-tracker/venv/bin/python /var/www/warframe-market-tracker/warframe_market_tracker/price_watcher.py

Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable price_watcher
systemctl start price_watcher
systemctl status price_watcher
```
### 9. Scheduled updates

```bash
crontab -e
```

Add:
```bash
0 4 * * * bash -c ' \
systemctl stop price_watcher && \
cd /var/www/warframe-market-tracker/warframe_market_tracker && \
/var/www/warframe-market-tracker/venv/bin/python manage.py load_market_items && \
systemctl start price_watcher \
' >> /var/log/warframe_cron.log 2>&1
```

Cron runs commands via /bin/sh, so bash -c is used for multi-line execution.

### Optional (UFW firewall)

```bash
ufw allow 80
ufw allow OpenSSH
ufw enable
```

## Known Limitations

- SQLite may cause database locking under concurrent writes
- This is mitigated by stopping the background worker during updates

## Usage
- Open the application in a browser
- Create an account
- Add items to track
- Set your desired selling price
- Wait for notification


## Project Structure

```
warframe-market-tracker/
├── warframe_market_tracker/
│   ├── warframe_market_tracker/
│   ├── tracker/
│   ├── staticfiles/
│   ├── manage.py
│   └── ...
├── nginx/
├── requirements.txt
├── gunicorn_config.py
└── README.md
```

## How to Run Locally

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

Open in browser:
http://127.0.0.1:8000

## Summary

This project demonstrates the ability to:

- Full-stack Django development
- Deployment to a VPS without containerization
- Configuration of Nginx and Gunicorn
- Background task processing with systemd
- Scheduled jobs using cron
- Debugging and resolving real-world issues (e.g., database locking)

## Project Purpose

This project was built to:

- Solve a real-world problem for Warframe players
- Practice backend development with Django
- Gain experience with deployment and server configuration
- Understand how background tasks and scheduling work in production-like environments