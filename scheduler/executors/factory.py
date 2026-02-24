"""
Factory: seleção do executor por extensão do arquivo ou por script_type (modelo).
"""
import os
import logging
from typing import Union

from .base import BaseExecutor
from .registry import get_registry

# Importa todos os executores para registro
from . import python_executor  # noqa: F401
from . import shell_executor
from . import batch_executor
from . import powershell_executor
from . import node_executor
from . import perl_executor
from . import ruby_executor
from . import go_executor

logger = logging.getLogger(__name__)

# ScriptType (valor do modelo) -> extensão
SCRIPT_TYPE_TO_EXT = {
    "python": ".py",
    "shell": ".sh",
    "batch": ".bat",
    "powershell": ".ps1",
    "node": ".js",
    "perl": ".pl",
    "ruby": ".rb",
    "go": ".go",
}


def get_executor(script_path_or_type: Union[str, None]) -> BaseExecutor:
    """
    Retorna uma instância do executor adequado.
    - script_path_or_type: caminho do script (ex: scripts/teste.py) ou tipo (ex: 'python').
    """
    registry = get_registry()

    ext = None
    if script_path_or_type:
        if script_path_or_type.startswith(".") or "/" in script_path_or_type or "\\" in script_path_or_type:
            ext = os.path.splitext(script_path_or_type)[1].lower()
        else:
            ext = SCRIPT_TYPE_TO_EXT.get(script_path_or_type.lower())

    if not ext:
        ext = ".py"
        logger.warning("Tipo de script não identificado, usando Python por padrão")

    ext = ext if ext.startswith(".") else f".{ext}"
    executor_class = registry.get(ext)
    if not executor_class:
        raise ValueError(
            f"Tipo de script não suportado: {ext}. "
            f"Tipos suportados: {', '.join(sorted(registry.keys()))}."
        )
    return executor_class()
