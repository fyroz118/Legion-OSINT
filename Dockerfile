FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config
COPY .env.example ./env.example
COPY README.md ANDROID_SETUP.md ./

RUN mkdir -p /app/data

CMD ["python", "-m", "app.bot"]
