# Python base image
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=warframe_market_tracker.settings

WORKDIR /app/warframe_market_tracker

# Collect static files
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "warframe_market_tracker.wsgi:application", "--bind", "0.0.0.0:8000"]