"""
Facade de execução de scripts: mantém a interface original do Orca
e delega para o sistema de executores (Strategy/Factory).
"""
import logging
from typing import Dict, Any, Optional

from .models import TaskStatus
from .executors import get_executor

logger = logging.getLogger(__name__)


class ScriptExecutor:
    """
    Executor de scripts – interface retrocompatível.
    Delega para executores por tipo (Python, Shell, PowerShell, etc.).
    """

    def build_command(self, script_path: str, script_type: str) -> list:
        """Constrói comando (retrocompatível)."""
        executor = get_executor(script_type or script_path)
        return executor.get_command(
            script_path,
            args=[],
            interpreter_path=None,
        )

    def execute(
        self,
        script_path: str,
        script_type: str,
        timeout: Optional[int] = None,
        base_dir: Optional[str] = None,
        args: Optional[list] = None,
        interpreter_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executa um script e retorna resultado (dict) – interface original.
        script_type: valor do modelo (python, shell, batch, powershell, node, perl, ruby, go).
        """
        executor = get_executor(script_type or script_path)
        result = executor.execute(
            script_path=script_path,
            timeout=timeout,
            base_dir=base_dir,
            args=args or [],
            interpreter_path=interpreter_path,
        )
        return result.to_dict()
