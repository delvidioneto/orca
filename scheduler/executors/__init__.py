"""
Pacote de executores de scripts do Orca.
Factory por extensão, validação de SO e interpretador.
"""
from .base import BaseExecutor, ExecutionResult
from .factory import get_executor
from .registry import get_platform, get_registry, check_interpreter

__all__ = [
    "BaseExecutor",
    "ExecutionResult",
    "get_executor",
    "get_registry",
    "get_platform",
    "check_interpreter",
]
