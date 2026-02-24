"""
Contrato base para executores de jobs do Core Engine.
Cada executor (Script, UiPath, Blue Prism) implementa run(task, base_dir) -> dict.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..models import Task


class JobExecutor(ABC):
    """
    Estratégia de execução de um job.
    Retorno padronizado: status, returncode, stdout, stderr, duration, error_message.
    """

    @abstractmethod
    def run(self, task: "Task", base_dir: str) -> Dict[str, Any]:
        """
        Executa o job da tarefa e retorna resultado padronizado.
        Levanta exceção em erro de configuração (ex.: executável não encontrado).
        """
        pass
