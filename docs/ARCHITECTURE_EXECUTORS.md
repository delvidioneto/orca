# Arquitetura de Executores de Scripts - Orca

## Proposta de refatoração

O Orca passa a usar um sistema de **executores** extensível, com padrão **Strategy** por tipo de script e **Factory** para seleção por extensão, mantendo retrocompatibilidade com `.py` e `.ps1`.

### Objetivos

- Suportar múltiplos tipos: `.py`, `.sh`, `.bat`, `.ps1`, `.js`, `.pl`, `.rb`, `.go`
- Identificação automática da extensão do arquivo
- Um executor dedicado por tipo (Strategy)
- Validação de **sistema operacional** (impedir execução incompatível)
- Validação de **interpretador no PATH** antes de executar
- Interface unificada: subprocess, stdout/stderr, exit code, argumentos dinâmicos
- Python com suporte a interpretador explícito (ex: `.venv/bin/python`)
- Logs estruturados e preparação para timeout por execução

---

## Estrutura de diretórios

```
scheduler/
├── executor.py              # Facade: mantém interface atual, delega para ExecutorFactory
├── executors/
│   ├── __init__.py          # Exporta get_executor(), ExecutorRegistry, tipos
│   ├── base.py              # BaseExecutor (classe abstrata)
│   ├── registry.py          # ExecutorRegistry, detecção de SO, which()
│   ├── factory.py           # ExecutorFactory (por extensão / tipo)
│   ├── python_executor.py   # PythonExecutor
│   ├── shell_executor.py    # ShellExecutor (.sh)
│   ├── batch_executor.py    # BatchExecutor (.bat)
│   ├── powershell_executor.py # PowerShellExecutor (.ps1)
│   ├── node_executor.py     # NodeExecutor (.js)
│   ├── perl_executor.py     # PerlExecutor (.pl)
│   ├── ruby_executor.py     # RubyExecutor (.rb)
│   └── go_executor.py       # GoExecutor (.go - go run ou binário)
├── models.py                # ScriptType estendido
└── ...
```

---

## Classe base (BaseExecutor)

- Método abstrato `get_command(script_path, args, interpreter_path=None) -> list`
- Método `validate_os() -> None` (levanta erro se SO incompatível)
- Método `validate_interpreter() -> None` (usa `shutil.which`, levanta se não existir)
- Método `execute(script_path, timeout, base_dir, args, interpreter_path) -> ExecutionResult`
- Execução via `subprocess.run`, captura stdout/stderr, returncode
- Se exit code != 0, retorna resultado com status FAILED (não lança exceção; o chamador decide)
- Log estruturado (logger) com script_path, tipo, duração, returncode

---

## Compatibilidade por sistema operacional

| Tipo   | Windows | Linux | macOS |
|--------|---------|-------|-------|
| .bat   | ✅      | ❌    | ❌    |
| .sh    | ❌      | ✅    | ✅    |
| .ps1   | ✅      | ✅*   | ✅*   |
| .py    | ✅      | ✅    | ✅    |
| .js    | ✅      | ✅    | ✅    |
| .pl    | ✅      | ✅    | ✅    |
| .rb    | ✅      | ✅    | ✅    |
| .go    | ✅      | ✅    | ✅    |

\* .ps1 no Linux/macOS exige PowerShell Core (`pwsh` ou `powershell`) no PATH.

---

## Factory e registro

- `ExecutorFactory.get_executor(script_path_or_type)` retorna instância do executor correto (por extensão do path ou por `script_type` do modelo).
- `ExecutorRegistry` mantém mapa extensão → classe e valida SO + interpretador antes de executar.

---

## Exemplo de uso

```python
from scheduler.executors import get_executor, ExecutionResult

# Por extensão (caminho)
executor = get_executor("scripts/meu_script.sh")
result = executor.execute(
    script_path="/app/scripts/meu_script.sh",
    timeout=30,
    base_dir="/app",
    args=["--env", "prod"],
    interpreter_path=None,
)
# result.status, result.stdout, result.stderr, result.returncode, result.duration

# Por tipo (valor do modelo Task.script_type)
executor = get_executor("python")
result = executor.execute(script_path="/app/scripts/teste.py", base_dir="/app")
assert result.returncode == 0
```

Uso via facade (retrocompatível):

```python
from scheduler.executor import ScriptExecutor

exec = ScriptExecutor()
out = exec.execute("/app/scripts/teste.py", "python", timeout=60, base_dir="/app")
# out é dict: status, returncode, stdout, stderr, duration, error_message, ...
```

---

## Retrocompatibilidade

- `scheduler.executor.ScriptExecutor` permanece: delega para `get_executor()` e chama `execute()` com a mesma assinatura de retorno (dict com status, returncode, stdout, stderr, duration, error_message).
- Tarefas existentes (.py, .ps1, .bat) continuam funcionando sem alteração.
