"""
Executor para PowerShell (.ps1).
Windows: powershell. Linux/macOS: pwsh (PowerShell Core) se existir.
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class PowerShellExecutor(BaseExecutor):
    extensions = [".ps1"]
    interpreter_name = "pwsh"
    allowed_os = None  # todos, mas no Unix exige pwsh ou powershell no PATH

    def validate_interpreter(self, interpreter_path: Optional[str] = None) -> None:
        if interpreter_path:
            super().validate_interpreter(interpreter_path)
            return
        if self.platform == "windows":
            if shutil.which("powershell"):
                return
            raise FileNotFoundError("PowerShell não encontrado no PATH (Windows).")
        # Linux/macOS: PowerShell Core
        if shutil.which("pwsh") or shutil.which("powershell"):
            return
        raise FileNotFoundError(
            "PowerShell Core (pwsh) não encontrado no PATH. "
            "Em Linux/macOS instale: https://docs.microsoft.com/powershell/scripting/install/installing-powershell"
        )

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        if interpreter_path:
            return [interpreter_path, "-ExecutionPolicy", "Bypass", "-File", script_path] + args
        if self.platform == "windows":
            exe = shutil.which("powershell") or "powershell"
        else:
            exe = shutil.which("pwsh") or shutil.which("powershell") or "pwsh"
        return [exe, "-ExecutionPolicy", "Bypass", "-File", script_path] + args


register_executor([".ps1"], PowerShellExecutor)
