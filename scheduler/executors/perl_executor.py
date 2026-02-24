"""
Executor para Perl (.pl).
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class PerlExecutor(BaseExecutor):
    extensions = [".pl"]
    interpreter_name = "perl"
    allowed_os = None

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        perl = interpreter_path or shutil.which("perl") or "perl"
        return [perl, script_path] + args


register_executor([".pl"], PerlExecutor)
