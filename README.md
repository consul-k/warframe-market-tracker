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

### 1. Clone repository

```bash
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
```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_ALLOWED_HOSTS=your_server_ip,localhost,127.0.0.1
DEBUG=False
```
### 4. Apply migrations and collect static
```bash
cd warframe_market_tracker
python manage.py migrate
python manage.py collectstatic --noinput
```
### 5. Run Gunicorn
```bash
gunicorn warframe_market_tracker.wsgi:application --bind 127.0.0.1:8000
```
### 6. Configure Nginx

Example config:
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
### 7. Background services

Start price watcher:
```bash
systemctl enable price_watcher
systemctl start price_watcher
```
### 8. Scheduled updates

Daily update of market items:
```bash
0 4 * * * /usr/bin/systemctl stop price_watcher && \
cd /var/www/warframe-market-tracker/warframe_market_tracker && \
/var/www/warframe-market-tracker/venv/bin/python manage.py load_market_items && \
/usr/bin/systemctl start price_watcher >> /var/log/warframe_cron.log 2>&1
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