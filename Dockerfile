FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GEE_PROJECT_ID=geoportal-513817

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec gunicorn --bind :${PORT} --workers 1 --threads 4 --timeout 420 webapp.main:app

