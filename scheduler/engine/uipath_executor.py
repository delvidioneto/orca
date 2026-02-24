"""
Executor de jobs UiPath via UiRobot CLI.
Requer Windows; valida presença do executável.
Futuro: integração via API REST do Orchestrator.
"""
import logging
import os
import platform
import subprocess
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..models import TaskStatus
from .base import JobExecutor

if TYPE_CHECKING:
    from ..models import Task

logger = logging.getLogger(__name__)

# Nomes comuns do executável UiPath (ordem de preferência)
UIPATH_EXECUTABLES = ["UiRobot.exe", "UiPath.Agent.exe", "UiPath.Executor.exe"]


def _find_uipath_executable(executable_path: str = None) -> str:
    """Retorna o caminho do UiRobot/UiPath.Agent. Levanta FileNotFoundError se não encontrar."""
    if executable_path and os.path.isfile(executable_path):
        return executable_path
    if platform.system() != "Windows":
        raise ValueError("UiPath só é suportado no Windows.")
    # PATH
    for name in UIPATH_EXECUTABLES:
        found = _which_win(name)
        if found:
            return found
    raise FileNotFoundError(
        "UiPath não encontrado. Instale o UiPath Robot ou informe executable_path em executor_config."
    )


def _which_win(executable: str) -> Optional[str]:
    """Simula which no Windows (PATH)."""
    path_env = os.environ.get("PATH", "")
    for folder in path_env.split(os.pathsep):
        full = os.path.join(folder.strip(), executable)
        if os.path.isfile(full):
            return full
    return None


class UiPathJobExecutor(JobExecutor):
    """
    Executa processos UiPath via CLI.
    executor_config esperado: process_file (caminho .xaml ou projeto), opcional executable_path.
    """

    def run(self, task: "Task", base_dir: str) -> Dict[str, Any]:
        config = task.executor_config or {}
        process_file = config.get("process_file") or config.get("project_path") or ""
        executable_path = config.get("executable_path")

        if not process_file:
            return _fail_result("executor_config deve conter 'process_file' (caminho .xaml ou projeto).")

        if platform.system() != "Windows":
            return _fail_result("UiPath só é suportado no Windows.")

        exe = _find_uipath_executable(executable_path)
        # Resolver path do processo
        if not os.path.isabs(process_file) and base_dir:
            process_file = os.path.normpath(os.path.join(base_dir, process_file))
        if not os.path.exists(process_file):
            return _fail_result(f"Arquivo de processo não encontrado: {process_file}")

        # UiRobot.exe -file "path\to\Main.xaml" (ou projeto)
        cmd = [exe, "-file", process_file]
        start = datetime.now()
        logger.info("Executando UiPath: %s", cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=task.timeout,
                shell=False,
                cwd=os.path.dirname(process_file) or None,
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds()
            return _fail_result(f"Timeout após {task.timeout}s", duration=duration)
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.exception("Erro ao executar UiPath: %s", e)
            return _fail_result(str(e), duration=duration)

        duration = (datetime.now() - start).total_seconds()
        status = TaskStatus.SUCCESS if result.returncode == 0 else TaskStatus.FAILED
        return {
            "status": status,
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "duration": duration,
            "error_message": result.stderr if result.returncode != 0 else "",
        }


def _fail_result(message: str, duration: float = 0.0) -> Dict[str, Any]:
    return {
        "status": TaskStatus.FAILED,
        "returncode": -1,
        "stdout": "",
        "stderr": message,
        "duration": duration,
        "error_message": message,
    }
