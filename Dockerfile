# Базовый образ с Python
FROM python:3.12-slim

# Устанавливаем зависимости ОС
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статические файлы Django
RUN python manage.py collectstatic --noinput

# Создаём пользователя для безопасности
RUN adduser --disabled-password appuser
USER appuser

# Команда запуска Gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "warframe_market_tracker.wsgi:application"]

