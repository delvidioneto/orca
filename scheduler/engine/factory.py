"""
Factory de executores de job por executor_type (Strategy).
"""
import logging
from typing import Dict, Type

from ..models import ExecutorType
from .base import JobExecutor
from .script_job_executor import ScriptJobExecutor
from .uipath_executor import UiPathJobExecutor
from .blueprism_executor import BluePrismJobExecutor

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, Type[JobExecutor]] = {
    ExecutorType.SCRIPT: ScriptJobExecutor,
    ExecutorType.UIPATH: UiPathJobExecutor,
    ExecutorType.BLUEPRISM: BluePrismJobExecutor,
}

_instances: Dict[str, JobExecutor] = {}


def get_job_executor(executor_type: str) -> JobExecutor:
    """Retorna a instância do executor adequado ao tipo da tarefa."""
    if executor_type not in _REGISTRY:
        logger.warning("executor_type '%s' desconhecido, usando script", executor_type)
        executor_type = ExecutorType.SCRIPT
    if executor_type not in _instances:
        _instances[executor_type] = _REGISTRY[executor_type]()
    return _instances[executor_type]
