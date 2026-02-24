"""
Executor para Batch (.bat) – somente Windows.
"""
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class BatchExecutor(BaseExecutor):
    extensions = [".bat"]
    interpreter_name = "cmd"
    allowed_os = ["windows"]

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        return ["cmd", "/c", script_path] + args


register_executor([".bat"], BatchExecutor)
