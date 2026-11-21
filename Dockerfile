FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

COPY backend backend
COPY frontend/dist frontend/dist

RUN useradd --create-home app && mkdir -p backend/resultados_tmp && chown -R app /app/backend/resultados_tmp
USER app

WORKDIR /app/backend
EXPOSE 8000
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "300", "--bind", "0.0.0.0:8000", "app:app"]
