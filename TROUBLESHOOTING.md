# 🔧 Troubleshooting - Orca

## Erro: Porta 8000 já está em uso

### Solução Rápida

```bash
# 1. Pare todos os containers do Orca
docker compose -f docker-compose.dev.yml down
# ou (se usar docker-compose antigo)
docker-compose -f docker-compose.dev.yml down

# 2. Remova containers órfãos
docker rm -f $(docker ps -aq --filter "name=orca") 2>/dev/null

# 3. Verifique se a porta está livre
lsof -i :8000

# 4. Se ainda houver processo, mate-o
lsof -ti :8000 | xargs kill -9

# 5. Tente novamente
docker compose -f docker-compose.dev.yml up -d
```

### Verificar o que está usando a porta

```bash
# Ver processos na porta 8000
lsof -i :8000

# Ver containers Docker rodando
docker ps

# Ver todos os containers (incluindo parados)
docker ps -a | grep orca
```

### Usar outra porta

Se precisar usar outra porta, edite o `docker-compose.dev.yml`:

```yaml
ports:
  - "8001:8000"  # Mude 8001 para a porta desejada
```

## Erro: Container não inicia

### Ver logs
```bash
docker compose -f docker-compose.dev.yml logs
```

### Rebuild completo
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d
```

## Erro: Permissão negada

### Ajustar permissões
```bash
sudo chown -R $USER:$USER ./logs ./media ./staticfiles
chmod +x docker-entrypoint.sh
```

## Erro: Banco de dados não conecta

### SQLite (dev)
```bash
# Verifique se o arquivo existe
ls -la db.sqlite3

# Remova e recrie
rm db.sqlite3
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### PostgreSQL (prod)
```bash
# Verifique se o container do banco está rodando
docker compose ps db

# Ver logs do banco
docker compose logs db

# Reinicie o banco
docker compose restart db
```

## Erro: Scheduler não inicia

### Verificar logs do scheduler
```bash
docker compose -f docker-compose.dev.yml logs web | grep scheduler
```

### Reiniciar scheduler manualmente
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py start_scheduler
```

## Limpar tudo e começar do zero

```bash
# Para containers
docker compose -f docker-compose.dev.yml down -v

# Remove imagens
docker rmi orca-web 2>/dev/null

# Remove volumes órfãos
docker volume prune -f

# Rebuild
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d
```

## Comandos úteis

```bash
# Ver status dos containers
docker compose -f docker-compose.dev.yml ps

# Ver logs em tempo real
docker compose -f docker-compose.dev.yml logs -f

# Executar comando no container
docker compose -f docker-compose.dev.yml exec web bash

# Criar superusuário
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Executar migrações
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

## Acessar por orca.localhost (não funciona)

O app pode ser acessado por **http://orca.localhost:8000** em vez de 127.0.0.1. Em alguns sistemas o nome `orca.localhost` não resolve sozinho; é preciso apontar no arquivo de hosts.

### macOS / Linux

1. Abra o arquivo de hosts (precisa de senha de admin):
   ```bash
   sudo nano /etc/hosts
   ```
2. Adicione esta linha no final (e salve com Ctrl+O, Enter, Ctrl+X):
   ```
   127.0.0.1   orca.localhost
   ```
3. No navegador, acesse: **http://orca.localhost:8000**

### Windows

1. Abra o Bloco de Notas **como Administrador**.
2. Abra o arquivo: `C:\Windows\System32\drivers\etc\hosts`
3. Adicione no final:
   ```
   127.0.0.1   orca.localhost
   ```
4. Salve e acesse no navegador: **http://orca.localhost:8000**

### Conferir se resolveu

No terminal:
```bash
ping orca.localhost
```
Deve responder com 127.0.0.1. Depois use **http://orca.localhost:8000** no navegador.

