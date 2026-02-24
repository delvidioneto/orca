"""
Registro de executores por extensão e validação de SO/interpretador.
"""
import logging
import platform
import shutil
from typing import Dict, Optional, Type

from .base import BaseExecutor

logger = logging.getLogger(__name__)

# Mapa extensão (.py, .sh, ...) -> classe do executor (preenchido em factory)
_REGISTRY: Dict[str, Type[BaseExecutor]] = {}


def register_executor(extensions: list, executor_class: Type[BaseExecutor]) -> None:
    """Registra um executor para as extensões dadas."""
    for ext in extensions:
        ext = ext if ext.startswith(".") else f".{ext}"
        _REGISTRY[ext.lower()] = executor_class


def get_platform() -> str:
    """Retorna 'windows', 'linux' ou 'darwin'."""
    return platform.system().lower()


def check_interpreter(name_or_path: str) -> bool:
    """Retorna True se o interpretador existir (PATH ou arquivo)."""
    import os
    if os.path.isfile(name_or_path):
        return True
    return shutil.which(name_or_path) is not None


def get_registry() -> Dict[str, Type[BaseExecutor]]:
    return dict(_REGISTRY)
