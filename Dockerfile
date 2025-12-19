FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/db /app/logs /app/staticfiles /app/media

EXPOSE 8000