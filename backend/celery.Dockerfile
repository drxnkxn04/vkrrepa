# celery.Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

# Установка системных зависимостей (нужно для компиляции psycopg2-binary)
RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла требований и установка зависимостей
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копирование всего остального кода приложения (включая manage.py и папку vkrtry2)
COPY . .

# Команда запуска Celery Worker
CMD ["celery", "-A", "vkrtry2", "worker", "--loglevel=info"]
