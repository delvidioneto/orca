"""
Executor para Shell Script (.sh) – Linux/Unix/macOS.
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class ShellExecutor(BaseExecutor):
    extensions = [".sh"]
    interpreter_name = "sh"
    allowed_os = ["linux", "darwin"]

    def validate_interpreter(self, interpreter_path: Optional[str] = None) -> None:
        if interpreter_path:
            super().validate_interpreter(interpreter_path)
            return
        if shutil.which("bash") or shutil.which("sh"):
            return
        raise FileNotFoundError("Nenhum interpretador shell encontrado no PATH (bash ou sh).")

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        cmd = shutil.which("bash") or shutil.which("sh") or "sh"
        return [cmd, script_path] + args


register_executor([".sh"], ShellExecutor)
