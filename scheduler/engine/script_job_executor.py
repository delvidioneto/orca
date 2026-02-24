"""
Executor de jobs do tipo script: delega para o ScriptExecutor existente.
"""
from typing import TYPE_CHECKING, Any, Dict

from ..executor import ScriptExecutor
from .base import JobExecutor

if TYPE_CHECKING:
    from ..models import Task


# Timeout padrão (segundos) quando a tarefa não define timeout – evita processo travado para sempre
DEFAULT_SCRIPT_TIMEOUT = 3600  # 1 hora


class ScriptJobExecutor(JobExecutor):
    """Executa tarefas do tipo script (.py, .ps1, etc.) usando o executor de scripts."""

    def __init__(self):
        self._script_executor = ScriptExecutor()

    def run(self, task: "Task", base_dir: str) -> Dict[str, Any]:
        if not task.script_path:
            return {
                "status": "failed",
                "returncode": -1,
                "stdout": "",
                "stderr": "script_path é obrigatório para executor_type=script",
                "duration": 0.0,
                "error_message": "script_path é obrigatório para executor_type=script",
            }
        timeout = task.timeout if task.timeout is not None and task.timeout > 0 else DEFAULT_SCRIPT_TIMEOUT
        return self._script_executor.execute(
            script_path=task.script_path,
            script_type=task.script_type or "python",
            timeout=timeout,
            base_dir=base_dir,
            interpreter_path=(task.script_interpreter_path or "").strip() or None,
        )
