"""
Executor para Go (.go) – via 'go run' ou binário compilado.
Por simplicidade, usamos 'go run' (requer Go instalado).
"""
import os
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class GoExecutor(BaseExecutor):
    extensions = [".go"]
    interpreter_name = "go"
    allowed_os = None

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        go = interpreter_path or shutil.which("go") or "go"
        return [go, "run", script_path] + args


register_executor([".go"], GoExecutor)
