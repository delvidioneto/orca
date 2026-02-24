"""
Executor para Node.js (.js).
"""
import shutil
from typing import List, Optional

from .base import BaseExecutor
from .registry import register_executor


class NodeExecutor(BaseExecutor):
    extensions = [".js"]
    interpreter_name = "node"
    allowed_os = None

    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        args = args or []
        node = interpreter_path or shutil.which("node") or "node"
        return [node, script_path] + args


register_executor([".js"], NodeExecutor)
