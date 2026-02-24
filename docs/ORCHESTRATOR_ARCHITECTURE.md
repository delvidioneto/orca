# Orca – Arquitetura do Orquestrador Universal

## Visão geral

O Orca evolui para um **orquestrador universal** (local, servidor dedicado e futuro cloud), mantendo execução de scripts e adicionando **RPA** (UiPath, Blue Prism), com Core Engine separado da interface e preparado para execução distribuída e API REST.

---

## Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│  Interface (Web UI, futura API REST, CLI)                        │
├─────────────────────────────────────────────────────────────────┤
│  Scheduler / Agendamento (APScheduler, DAG, triggers)            │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine (JobRunner, lock, retry, timeout, métricas)           │
├─────────────────────────────────────────────────────────────────┤
│  Executors (Strategy + Factory)                                  │
│  • ScriptExecutor (py, sh, bat, ps1, js, ...)                    │
│  • UiPathExecutor (UiRobot CLI)                                  │
│  • BluePrismExecutor (AutomateC.exe)                             │
├─────────────────────────────────────────────────────────────────┤
│  Persistência (Task, TaskExecution, Pipeline)                    │
└─────────────────────────────────────────────────────────────────┘
```

- **Engine** é independente da UI: pode ser chamado por Web, API, workers ou filas.
- **Executors** são plugáveis: mesmo contrato (run → status, stdout, stderr, returncode); novos tipos (outros RPAs, jobs cloud) entram por registro.

---

## Core Engine

- **Responsabilidades:** selecionar executor (Factory), aplicar **lock** (evitar execução duplicada do mesmo job), **timeout** e **retry** configuráveis, gravar **histórico** (TaskExecution) e **logs estruturados**.
- **Lock:** antes de iniciar, verifica se já existe execução RUNNING para o mesmo `task_id`; se existir, não inicia (ou enfileira para depois).
- **Status:** Pending → Running → Success/Failed (já existentes em TaskExecution).
- **Métricas:** derivadas do histórico (contagem por status, duração média, etc.) – atual modelo já suporta; métricas agregadas podem ser adicionadas depois.

---

## Executors (Strategy + Factory)

| Executor         | Tipo   | SO        | Validação              | Uso principal                    |
|------------------|--------|-----------|------------------------|-----------------------------------|
| ScriptExecutor   | script | Todos     | Interpretador no PATH  | .py, .sh, .bat, .ps1, .js, ...   |
| UiPathExecutor   | uipath | Windows   | UiRobot/UiPath.Agent   | Processos UiPath (.xaml / CLI)    |
| BluePrismExecutor| blueprism | Windows | AutomateC.exe         | Processos Blue Prism (/run)      |

- Cada executor expõe: `run(task, base_dir) → ExecutionResult` (ou dict compatível).
- Factory: `get_job_executor(task.executor_type)` retorna a implementação correta.

---

## RPA – Configuração por tarefa

- **UiPath:** `executor_config`: `process_file` (caminho .xaml), opcional `executable_path` (UiRobot.exe ou UiPath.Agent.exe). Futuro: Orchestrator API (fila, asset).
- **Blue Prism:** `executor_config`: `process_name`, `user`, `password` (ou `sso: true`), opcional `resource`. Futuro: API Blue Prism.

**Guia completo (interface, campos JSON, exemplos):** [RPA – UiPath e Blue Prism](/documentacao/rpa/)

---

## Evolução futura

- **Execução distribuída:** Engine publica jobs em fila (Redis/RabbitMQ); workers consomem e chamam o mesmo Core Engine.
- **API REST:** Endpoints para disparar pipeline/tarefa, consultar status e histórico (Engine como serviço).
- **Worker nodes:** Múltiplas instâncias do Orca só precisam de fila + lock distribuído (ex.: Redis lock por `task_id`).

---

## Interpretador do script (venv do usuário)

- Orca em **Docker não usa venv próprio**; dependências vão na imagem.
- O campo **script_interpreter_path** na Task é opcional: quando preenchido (ex: `/app/venv/bin/python`), o Orca executa o script com esse interpretador — o venv é do *ambiente do usuário*, não do Orca.
- Em branco, usa o interpretador do PATH (comportamento padrão).

## Compatibilidade

- Tarefas existentes continuam com `executor_type=script` (default); `script_path` e `script_type` seguem iguais.
- Novas tarefas podem escolher `executor_type`: script, uipath, blueprism; para RPA, `executor_config` guarda os parâmetros específicos.
