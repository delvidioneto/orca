# Orca – Linux

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

Em produção, use um servidor de aplicação (gunicorn/uWSGI) atrás de um proxy reverso (nginx). Para Docker, use `install/docker/`.
