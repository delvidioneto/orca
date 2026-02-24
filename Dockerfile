FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=orca_project.settings

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto
COPY . .

# Versão para o rodapé (build-arg opcional: docker build --build-arg VERSION=$(git describe --tags --always))
ARG VERSION=0.0.0
RUN echo "$VERSION" > /app/VERSION

# Cria diretórios necessários
RUN mkdir -p /app/logs /app/staticfiles /app/media /app/scripts

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput || true

# Expõe a porta
EXPOSE 8000

# Script de inicialização
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Comando padrão
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "orca_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

