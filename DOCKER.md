# 🐳 Guia Docker - Orca

Este guia explica como executar o Orca usando Docker e Docker Compose.

## 📋 Pré-requisitos

- Docker instalado (versão 20.10 ou superior)
- Docker Compose instalado (versão 2.0 ou superior)

Verifique a instalação:
```bash
docker --version
docker-compose --version
```

## 🚀 Início Rápido

### 1. Build e Start (Desenvolvimento)

```bash
# Build da imagem
docker-compose -f docker-compose.dev.yml build

# Inicia os containers
docker-compose -f docker-compose.dev.yml up -d

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f
```

### 2. Acessar a Aplicação

Abra seu navegador em: `http://localhost:8000`

**Credenciais padrão (criadas automaticamente):**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **IMPORTANTE**: Altere a senha após o primeiro login!

### 3. Parar os Containers

```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml down

# Produção
docker-compose down
```

## 📁 Estrutura de Volumes

O Docker Compose monta os seguintes volumes:

- `./scripts` → Scripts a serem executados (somente leitura)
- `./logs` → Logs do sistema
- `./media` → Arquivos de mídia
- `./db.sqlite3` → Banco de dados SQLite (desenvolvimento)
- `./staticfiles` → Arquivos estáticos coletados

## 🔧 Configurações

### Variáveis de Ambiente

**Desenvolvimento** (`docker-compose.dev.yml`):
```yaml
environment:
  - DEBUG=True                    # True/False
  - CREATE_SUPERUSER=true          # Cria admin/admin123 automaticamente
  - DATABASE=sqlite                # sqlite
  - TIME_ZONE=America/Sao_Paulo    # Timezone
```

**Produção** (`docker-compose.yml`):
```yaml
environment:
  - DEBUG=False                    # False em produção
  - CREATE_SUPERUSER=false         # Crie manualmente
  - DATABASE=postgres              # PostgreSQL
  - DB_PASSWORD=${DB_PASSWORD}     # Configure via variável
  - SECRET_KEY=${SECRET_KEY}       # Configure via variável
  - TIME_ZONE=America/Sao_Paulo    # Timezone
```

### Usando Produção (PostgreSQL)

```bash
# Configure variáveis de ambiente
export SECRET_KEY="sua-chave-secreta"
export DB_PASSWORD="senha-segura"

# Inicie (usa docker-compose.yml por padrão)
docker-compose up -d
```

## 🛠️ Comandos Úteis

### Ver logs
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml logs -f web

# Produção
docker-compose logs -f web
```

### Executar comandos Django
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Produção
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py start_scheduler
```

### Acessar shell do container
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml exec web bash

# Produção
docker-compose exec web bash
```

### Rebuild após mudanças
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d

# Produção
docker-compose build --no-cache
docker-compose up -d
```

### Limpar tudo (cuidado!)
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml down -v  # Remove volumes também

# Produção
docker-compose down
docker-compose down -v  # Remove volumes também (apaga dados!)
docker-compose down --rmi all  # Remove imagens
```

## 📦 Produção

### Usando docker-compose.yml (padrão para produção)

```bash
# 1. Configure variáveis de ambiente
export SECRET_KEY="sua-chave-secreta-super-segura"
export DB_PASSWORD="senha-segura-do-banco"

# 2. Inicie com configuração de produção (usa docker-compose.yml por padrão)
docker-compose up -d

# 3. Crie superusuário manualmente
docker-compose exec web python manage.py createsuperuser
```

### Usando Gunicorn

O `docker-compose.yml` (produção) já usa Gunicorn com 4 workers. Para ajustar:

```yaml
command: gunicorn orca_project.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

### Nginx (Reverso Proxy)

Exemplo de configuração Nginx:

```nginx
server {
    listen 80;
    server_name orca.exemplo.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
```

## 🔍 Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker-compose -f docker-compose.dev.yml logs web  # Dev
docker-compose logs web  # Prod

# Verificar se a porta está em uso
lsof -i :8000
```

### Erro de permissão
```bash
# Ajustar permissões dos volumes
sudo chown -R $USER:$USER ./logs ./media ./staticfiles
```

### Banco de dados não conecta
```bash
# Verificar se PostgreSQL está rodando (produção)
docker-compose ps db

# Ver logs do PostgreSQL
docker-compose logs db
```

### Scripts não executam
- Verifique se os scripts estão em `./scripts/`
- Verifique permissões: `chmod +x scripts/*.py`
- Verifique logs: 
  - Dev: `docker-compose -f docker-compose.dev.yml logs web`
  - Prod: `docker-compose logs web`

### Scheduler não inicia
```bash
# Verificar logs
docker-compose -f docker-compose.dev.yml logs web | grep scheduler  # Dev
docker-compose logs web | grep scheduler  # Prod

# Reiniciar container
docker-compose -f docker-compose.dev.yml restart web  # Dev
docker-compose restart web  # Prod
```

## 📝 Notas Importantes

1. **Scripts .bat e .ps1**: Só funcionam no Windows. No Linux/Mac dentro do Docker, use apenas scripts Python.

2. **Persistência**: Os dados são salvos nos volumes. Se você remover os volumes (`docker-compose down -v`), perderá os dados!

3. **Performance**: Para produção, considere usar PostgreSQL ao invés de SQLite.

4. **Segurança**: 
   - Altere `SECRET_KEY` em produção
   - Altere senhas padrão
   - Configure `ALLOWED_HOSTS` no settings.py
   - Use HTTPS com Nginx

## 🚀 Deploy em Servidor

### 1. Clone o repositório no servidor
```bash
git clone <seu-repo> /opt/orca
cd /opt/orca
```

### 2. Configure variáveis de ambiente
```bash
export SECRET_KEY="sua-chave-secreta"
export DB_PASSWORD="senha-segura"
```

### 3. Build e start
```bash
docker-compose build
docker-compose up -d
```

### 4. Configure Nginx (opcional)
Siga o exemplo acima.

### 5. Configure SSL (recomendado)
Use Let's Encrypt com Certbot.

## 📚 Recursos Adicionais

- [Documentação Docker](https://docs.docker.com/)
- [Documentação Docker Compose](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

