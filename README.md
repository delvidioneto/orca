# 🐋 Orca – Orquestrador de Scripts Profissional

Orca é um sistema completo de orquestração de scripts similar ao Airflow, desenvolvido em Django com APScheduler. Permite criar pipelines complexos com dependências, agendamento flexível e interface web amigável.

## ✨ Características

- ✅ **Execução não-bloqueante** com ThreadPoolExecutor
- ✅ **Pipelines com DAGs** - Dependências entre tarefas
- ✅ **Múltiplos tipos de script** - Python (.py), Batch (.bat), PowerShell (.ps1)
- ✅ **Agendamento flexível** - Diário, semanal, mensal, quinzenal, cron
- ✅ **Interface web moderna** - Dashboard e gerenciamento completo
- ✅ **Sistema de retry** - Retentativas automáticas em caso de falha
- ✅ **Histórico completo** - Todas as execuções são registradas
- ✅ **Escalável** - Suporta múltiplas execuções paralelas

## 🚀 Instalação

### Opção 1: Docker (Recomendado) 🐳

A forma mais fácil de executar o Orca é usando Docker. **O Orca não usa venv próprio no container** — as dependências vão na imagem. O venv é do *script do usuário*: na tarefa você pode informar o caminho do Python do ambiente dele (ex: `/app/venv/bin/python`) e o Orca executa o script com esse interpretador.

**Desenvolvimento:**
```bash
# Build e start
docker-compose -f docker-compose.dev.yml up -d

# Acesse http://localhost:8000
# Login: admin / admin123
```

**Produção:**
```bash
# Configure variáveis
export SECRET_KEY="sua-chave-secreta"
export DB_PASSWORD="senha-segura"

# (Opcional) Versão exibida no rodapé da aplicação
export ORCA_VERSION=$(git describe --tags --always)

# Build e start
docker-compose up -d
```

Veja o [Guia Docker completo](DOCKER.md) para mais detalhes.

### Opção 3: Launcher (Windows)

Para Windows há um launcher que sobe o Orca (Docker ou Sem Docker), coloca o ícone na bandeja e pode iniciar com o Windows. Veja [launcher/README.md](launcher/README.md).

### Opção 2: Instalação Manual

#### 1. Clone o repositório

```bash
cd orca
```

#### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

#### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

#### 4. Configure o banco de dados

```bash
python manage.py migrate
```

#### 5. Crie um superusuário

```bash
python manage.py createsuperuser
```

#### 6. Execute o servidor

```bash
python manage.py runserver
```

O scheduler será iniciado automaticamente quando o servidor Django iniciar.

## 📖 Uso

### Acessando a Interface Web

1. Acesse `http://localhost:8000`
2. Faça login com o superusuário criado
3. Navegue pelo menu lateral:
   - **Dashboard**: Visão geral do sistema
   - **Pipelines**: Gerenciar pipelines e tarefas
   - **Execuções**: Histórico de execuções

### Criando um Pipeline

1. Vá em **Pipelines** → **Novo Pipeline**
2. Preencha nome e descrição
3. Clique em **Salvar**

### Adicionando Tarefas

1. Abra o pipeline desejado
2. Clique em **Nova Tarefa**
3. Configure:
   - **Nome**: Nome da tarefa
   - **Script**: Caminho do script (ex: `scripts/meu_script.py`)
   - **Tipo**: Python, Batch ou PowerShell
   - **Interpretador** (opcional): Caminho do Python do ambiente do usuário (ex: `/app/venv/bin/python`). Em branco usa o do sistema (PATH). Útil quando o script depende de um venv montado no container.
   - **Agendamento**: Escolha o tipo e configure (veja exemplos abaixo)
   - **Dependências**: Selecione tarefas que devem executar antes
   - **Retries**: Número de tentativas em caso de falha

### Tipos de Agendamento

#### Diário
```json
{"hour": 9, "minute": 0}
```

#### Semanal (Toda Segunda-feira às 9h)
```json
{"day_of_week": 0, "hour": 9, "minute": 0}
```
- 0 = Segunda-feira
- 1 = Terça-feira
- ...
- 6 = Domingo

#### Mensal (Dia 1 de cada mês às 9h)
```json
{"day": 1, "hour": 9, "minute": 0}
```

#### Quinzenal (A cada 2 semanas, Segunda às 9h)
```json
{"day_of_week": 0, "hour": 9, "minute": 0}
```
O sistema automaticamente executa a cada 2 semanas.

#### Intervalo (A cada 30 minutos)
```json
{"minutes": 30}
```

#### Cron Completo
Use o tipo "Cron" e configure:
```json
{
  "minute": "*/5",
  "hour": "*",
  "day_of_week": "0-4"
}
```

## 🏗️ Estrutura do Projeto

```
orca/
├── orca_project/          # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   ├── version.py         # Versão (Git / VERSION / ORCA_VERSION)
│   └── wsgi.py
├── accounts/              # App de autenticação
├── dashboard/             # App do dashboard
├── scheduler/             # App principal
│   ├── models.py          # Pipeline, Task, TaskExecution
│   ├── executor.py        # Executor de scripts
│   ├── scheduler_manager.py  # Gerenciador APScheduler
│   ├── dag_manager.py     # Gerenciador de DAGs
│   └── views.py           # Views CRUD
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── scripts/               # Scripts a serem executados
├── logs/                  # Logs do sistema
├── docs/                  # Documentação (exibida na interface)
├── githooks/              # Hooks Git (ex.: pre-commit para atualizar VERSION)
├── launcher/              # Launcher Windows (bandeja, Docker/Sem Docker)
├── manage.py
├── requirements.txt
├── VERSION                # Versão (fallback quando não há Git)
└── README.md
```

## 🔧 Configuração Avançada

### Versão (rodapé da aplicação)

A versão exibida no rodapé e no launcher é obtida nesta ordem:

1. **Variável de ambiente `ORCA_VERSION`** — útil em Docker: `ORCA_VERSION=$(git describe --tags --always) docker compose up -d`
2. **Git** — `git describe --tags --always` na raiz do projeto
3. **Arquivo `VERSION`** na raiz — uma linha com a versão (ex.: `v1.0.1`)
4. **Fallback** — `0.0.0`

**Atualizar `VERSION` automaticamente a cada commit (recomendado):** instale o hook de pre-commit uma vez:

```bash
cp githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

A partir daí, em todo `git commit` o arquivo `VERSION` é atualizado com `git describe --tags --always` e incluído no próprio commit. Assim você não precisa atualizar o `VERSION` manualmente antes do push.

### Executando o Scheduler Separadamente

Se preferir executar o scheduler em um processo separado:

```bash
python manage.py start_scheduler
```

### Configurando Timezone

Edite `orca_project/settings.py`:

```python
TIME_ZONE = 'America/Sao_Paulo'  # Ajuste conforme necessário
```

### Ajustando Pool de Threads

Edite `scheduler/scheduler_manager.py`:

```python
executors = {
    'default': ThreadPoolExecutor(20),  # Ajuste o número de threads
}
```

## 📝 Exemplos de Scripts

### Python (scripts/exemplo.py)
```python
from datetime import datetime
import sys

print(f"Script executado às {datetime.now()}")
sys.exit(0)  # 0 = sucesso
```

### Batch (scripts/exemplo.bat)
```batch
@echo off
echo Script batch executado
exit /b 0
```

### PowerShell (scripts/exemplo.ps1)
```powershell
Write-Host "Script PowerShell executado"
exit 0
```

## 🐛 Troubleshooting

### Scheduler não inicia
- Verifique os logs em `logs/orca.log`
- Certifique-se de que o Django está rodando
- Tente executar manualmente: `python manage.py start_scheduler`

### Scripts não executam
- Verifique se o caminho do script está correto
- Certifique-se de que o script tem permissão de execução
- Verifique os logs de execução na interface web

### Dependências não funcionam
- Certifique-se de que as tarefas dependentes estão ativas
- Verifique se não há ciclos nas dependências (DAG inválido)

## 📄 Licença

Este projeto é de código aberto e está disponível para uso livre.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.
