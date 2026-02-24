"""
Executor para Ruby (.rb).
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class RubyExecutor(BaseExecutor):
    extensions = [".rb"]
    interpreter_name = "ruby"
    allowed_os = None

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        ruby = interpreter_path or shutil.which("ruby") or "ruby"
        return [ruby, script_path] + args


register_executor([".rb"], RubyExecutor)
