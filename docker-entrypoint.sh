#!/bin/bash
set -e

echo "🐋 Iniciando Orca..."

# Instala netcat se não estiver disponível (para verificar PostgreSQL)
if ! command -v nc &> /dev/null; then
    echo "Instalando netcat..."
    apt-get update && apt-get install -y netcat-openbsd || true
fi

# Aguarda o banco de dados estar pronto (se usar PostgreSQL)
if [ "$DATABASE" = "postgres" ]; then
    echo "Aguardando PostgreSQL..."
    until nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
        echo "Aguardando PostgreSQL em ${DB_HOST:-db}:${DB_PORT:-5432}..."
        sleep 1
    done
    echo "PostgreSQL está pronto!"
fi

# Cria diretório data se não existir (para SQLite)
echo "Criando diretório data..."
mkdir -p /app/data
chmod 777 /app/data

# Garante que o diretório pai do banco existe e tem permissões
touch /app/data/.keep
chmod 777 /app/data/.keep || true

# Executa migrações
echo "Executando migrações..."
python manage.py migrate --noinput

# Coleta arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || true

# Cria superusuário se não existir (apenas em desenvolvimento e se não houver nenhum superusuário)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Verificando superusuários..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
# Só cria se não houver NENHUM superusuário
if not User.objects.filter(is_superuser=True).exists():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@orca.local', 'admin123')
        print('Superusuário padrão criado: admin/admin123')
    else:
        print('Usuário admin já existe, mas não é superusuário')
else:
    print('Já existem superusuários no sistema')
EOF
fi

# Executa o comando passado
exec "$@"

