FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=orca_project.settings

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Versão (build-arg opcional: --build-arg VERSION=v1.0.0). App lê install/version/VERSION (COPY . . já coloca o arquivo).
ARG VERSION=0.0.0
RUN mkdir -p /app/install/version && echo "$VERSION" > /app/install/version/VERSION

RUN mkdir -p /app/logs /app/staticfiles /app/media /app/scripts

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

COPY install/docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "orca_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
