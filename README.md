# 🐋 Orca – Orquestrador de Scripts

## O que é o Orca

O **Orca** é um sistema de orquestração de scripts para automação e agendamento de tarefas. Inspirado em ferramentas como o Airflow, ele permite criar **pipelines** com dependências entre tarefas (DAGs), agendar execuções em horários fixos ou por intervalo e acompanhar tudo por uma **interface web**. É desenvolvido em **Django** e usa **APScheduler** para o agendamento, com suporte a Python, Batch, PowerShell e outros tipos de script.

Ideal para rotinas de ETL, relatórios agendados, integrações e qualquer fluxo que precise rodar em horários definidos ou após a conclusão de outras tarefas.

---

## Características

- **Pipelines com DAGs** — Defina dependências entre tarefas; cada uma só roda quando as anteriores forem concluídas.
- **Agendamento flexível** — Diário, semanal, mensal, quinzenal, por intervalo ou cron; vários horários por dia na mesma tarefa.
- **Múltiplos tipos de script** — Python (.py), Batch (.bat), PowerShell (.ps1), Node, Shell, etc.
- **Interface web** — Dashboard, listagem de pipelines, tarefas e histórico de execuções.
- **Execução paralela** — Várias tarefas podem rodar ao mesmo tempo; execução não bloqueante.
- **Retentativas** — Configure número de retries e delay em caso de falha.
- **Histórico** — Todas as execuções ficam registradas com status e logs.

---

## Instalação

### Com Docker (recomendado)

A forma mais simples é usar Docker. O Orca sobe com banco (PostgreSQL em produção ou SQLite em dev) e não usa venv dentro do container — dependências vão na imagem. Para scripts do usuário, você pode informar o caminho do interpretador na tarefa (ex.: Python de um venv montado).

**Desenvolvimento:**

```bash
docker-compose -f docker-compose.dev.yml up -d
# Acesse http://localhost:8000 — login: admin / admin123
```

**Produção:**

```bash
export SECRET_KEY="sua-chave-secreta"
export DB_PASSWORD="senha-segura"
# Opcional: export ORCA_VERSION=1.0.2
docker-compose up -d
```

Detalhes: [DOCKER.md](DOCKER.md).

### Sem Docker (manual)

1. **Clone e entre na pasta do projeto**

   ```bash
   cd orca
   ```

2. **Crie e ative um ambiente virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   # ou: venv\Scripts\activate   # Windows
   ```

3. **Instale dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Banco e superusuário**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Inicie o servidor**

   ```bash
   python manage.py runserver
   ```

   O scheduler sobe junto com o Django. Acesse `http://localhost:8000`.

### Windows com .bat

Na raiz do projeto há scripts para Windows:

| Arquivo | Função |
|--------|--------|
| **IniciarOrca.bat** | Cria `.venv` se não existir, instala dependências, roda `migrate` e sobe o servidor (janela de console). |
| **IniciarOrca.vbs** | Inicia o Orca em segundo plano (sem janela), chamando o `IniciarOrca.bat`. |
| **PararOrca.bat** | Encerra o processo do Orca. |
| **AdicionarInicioWindows.bat** | Adiciona início automático do Orca ao ligar o PC (uma execução). |
| **RemoverInicioWindows.bat** | Remove o início automático. |

Requisito: Python no PATH (`python` ou `py`). Para rodar sem ver a janela, use **IniciarOrca.vbs**.

**Launcher (bandeja do sistema):** para ícone na bandeja, iniciar com o Windows e opção Docker ou Sem Docker, use o launcher em [launcher/README.md](launcher/README.md).

---

## Uso

### Interface web

1. Acesse `http://localhost:8000` e faça login.
2. Menu principal:
   - **Dashboard** — Visão geral.
   - **Pipelines** — Criar e editar pipelines e tarefas.
   - **Execuções** — Histórico de execuções.

### Criar pipeline e tarefas

1. **Pipelines** → **Novo Pipeline** → nome e descrição → Salvar.
2. Abra o pipeline → **Nova Tarefa** e configure:
   - Nome, script (ex.: `scripts/meu_script.py`), tipo (Python, Batch, PowerShell…).
   - **Interpretador** (opcional): caminho do Python/venv (ex.: `/app/venv/bin/python`).
   - **Agendamento**: JSON conforme os exemplos abaixo.
   - **Dependências**: tarefas que precisam rodar antes.
   - **Retries** e delay entre tentativas.

### Tipos de agendamento (JSON)

**Diário (um horário):**

```json
{"hour": 9, "minute": 0}
```

**Diário (vários horários na mesma tarefa):**

```json
[
  {"hour": 8, "minute": 0},
  {"hour": 10, "minute": 30},
  {"hour": 14, "minute": 18}
]
```

**Semanal (ex.: segunda às 9h):** `0` = segunda … `6` = domingo

```json
{"day_of_week": 0, "hour": 9, "minute": 0}
```

**Mensal (dia 1 às 9h):**

```json
{"day": 1, "hour": 9, "minute": 0}
```

**Quinzenal (a cada 2 semanas):**

```json
{"day_of_week": 0, "hour": 9, "minute": 0}
```

**Intervalo (ex.: a cada 30 min):**

```json
{"minutes": 30}
```

**Cron completo:**

```json
{"minute": "*/5", "hour": "*", "day_of_week": "0-4"}
```

---

## Estrutura do projeto

```
orca/
├── orca_project/          # Configurações Django (settings, urls, version, wsgi)
├── accounts/              # Autenticação
├── dashboard/             # Dashboard
├── scheduler/             # Pipelines, tarefas, agendamento (APScheduler), executor
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── scripts/               # Scripts a serem executados
├── logs/                  # Logs do sistema
├── docs/                  # Documentação (interface)
├── githooks/              # Hook pre-commit (atualiza VERSION)
├── launcher/              # Launcher Windows (bandeja)
├── manage.py
├── requirements.txt
├── VERSION                # Versão exibida (semântica)
├── IniciarOrca.bat        # Iniciar Orca no Windows (sem Docker)
├── IniciarOrca.vbs        # Iniciar em segundo plano
├── PararOrca.bat
└── README.md
```

---

## Configuração avançada

### Versão (rodapé)

Ordem de leitura: variável **`ORCA_VERSION`** → arquivo **`VERSION`** → Git → `0.0.0`. Para gerar `VERSION` automaticamente a cada commit (ex.: `v1.0.2`):

```bash
cp githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

O hook incrementa o patch quando há commits após a última tag (ex.: tag `v1.0.1` + 1 commit → `v1.0.2`).

### Scheduler em processo separado

```bash
python manage.py start_scheduler
```

### Timezone

Em `orca_project/settings.py`:

```python
TIME_ZONE = 'America/Sao_Paulo'
```

### Pool de threads

Em `scheduler/scheduler_manager.py`:

```python
executors = { 'default': ThreadPoolExecutor(20) }  # Ajuste conforme necessário
```

---

## Troubleshooting

| Problema | O que verificar |
|----------|------------------|
| **Scheduler não inicia** | Logs em `logs/orca.log`; Django rodando; teste manual: `python manage.py start_scheduler`. |
| **Scripts não executam** | Caminho do script correto; permissão de execução; logs da execução na interface. |
| **Dependências não funcionam** | Tarefas dependentes ativas; ausência de ciclos no DAG. |
| **Erro ao iniciar no Windows (.bat)** | Python no PATH (`python` ou `py`); mensagens em `orca_err.txt` na raiz do projeto. |

---

## Licença

Este projeto é de código aberto e está disponível para uso conforme os termos do repositório.

---

## Contribuindo

Contribuições são bem-vindas: correções, melhorias de documentação e novas funcionalidades. Abra uma **issue** para discussão ou envie um **pull request** com as alterações.
