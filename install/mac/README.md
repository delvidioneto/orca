# Orca – macOS

Execute na **raiz do projeto**.

**1. Ambiente virtual e dependências**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Migrações e servidor**
```bash
export DATABASE=sqlite
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
```

Acesse: http://127.0.0.1:8000

Para rodar em segundo plano (launcher com ícone na bandeja), use o app em `launcher/` (requer dependências do launcher).
