FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /srv

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/
COPY data/raw/ data/raw/

WORKDIR /srv/backend
# El modelo se entrena al construir la imagen, así el contenedor arranca al instante.
RUN python -m scripts.build_model

EXPOSE 5000
CMD gunicorn "app:create_app()" --bind 0.0.0.0:${PORT} --workers 2 --timeout 120
