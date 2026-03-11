#!/usr/bin/env bash
# Inicia o Orca na raiz do projeto. Uso: install/linux/run.sh (execute da raiz)
set -e
cd "$(dirname "$0")/../.."
export DATABASE=sqlite
if [ ! -d .venv ]; then
    echo "Criando .venv..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python manage.py migrate --noinput
echo "Acesse: http://127.0.0.1:8000"
exec .venv/bin/python manage.py runserver 0.0.0.0:8000
