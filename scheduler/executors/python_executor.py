"""
Executor para scripts Python (.py).
Suporta interpretador explícito (ex: .venv/bin/python).
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class PythonExecutor(BaseExecutor):
    extensions = [".py"]
    interpreter_name = None  # validado em validate_interpreter (python3 ou python)
    allowed_os = None  # todos

    def validate_interpreter(self, interpreter_path: Optional[str] = None) -> None:
        if interpreter_path:
            super().validate_interpreter(interpreter_path)
            return
        if shutil.which("python3") or shutil.which("python"):
            return
        raise FileNotFoundError(
            "Nenhum interpretador Python encontrado no PATH (python3 ou python). "
            "Instale-o ou informe o caminho no campo interpretador."
        )

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        if interpreter_path:
            return [interpreter_path, script_path] + args
        python = shutil.which("python3") or shutil.which("python") or "python"
        return [python, script_path] + args


register_executor([".py"], PythonExecutor)
