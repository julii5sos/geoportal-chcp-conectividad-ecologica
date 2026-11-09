FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GEE_PROJECT_ID=geoportal-513817 \
    WEB_MAX_REQUEST_BYTES=1048576 \
    WEB_MAX_COORDINATES=5000 \
    WEB_MAX_ANALYSIS_AREA_HA=345000 \
    WEB_MAX_MAP_FEATURES=1500 \
    WEB_RESULT_CACHE_ENTRIES=6 \
    WEB_RESULT_CACHE_TTL=3600 \
    WEB_MAX_CONCURRENT_ANALYSES=1 \
    WEB_ANALYSIS_RATE_LIMIT=4 \
    WEB_DOWNLOAD_RATE_LIMIT=20 \
    WEB_RATE_LIMIT_WINDOW_SECONDS=600 \
    WEB_TRUST_PROXY_HEADERS=1

WORKDIR /app

COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

RUN addgroup --system --gid 10001 app && \
    adduser --system --uid 10001 --ingroup app --home /app app

COPY --chown=app:app . .

USER 10001:10001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/health', timeout=3)"

CMD ["sh", "-c", "exec gunicorn --bind :${PORT} --workers 1 --threads ${WEB_GUNICORN_THREADS:-4} --timeout ${WEB_WORKER_TIMEOUT:-540} --graceful-timeout 30 --keep-alive 5 --max-requests 50 --max-requests-jitter 10 --access-logfile - --error-logfile - webapp.main:app"]

