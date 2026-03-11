# Orca – Docker

Pode ser executado **de dentro desta pasta** (`install/docker`) ou da raiz do projeto.

**Desta pasta (install/docker):**
```bash
cd install/docker

# Produção (PostgreSQL)
docker compose -f docker-compose.yml up -d

# Desenvolvimento (SQLite)
docker compose -f docker-compose.dev.yml up
```

**Da raiz do projeto:**
```bash
# Produção
docker compose -f install/docker/docker-compose.yml up -d

# Desenvolvimento
docker compose -f install/docker/docker-compose.dev.yml up
```

**Desenvolvimento com Postgres (perfil opcional):**
```bash
docker compose -f docker-compose.dev.yml --profile postgres up
```

Variáveis opcionais: `DB_PASSWORD`, `SECRET_KEY`, `ORCA_VERSION`, `CREATE_SUPERUSER`. Veja `DOCKER.md` na raiz para detalhes.
