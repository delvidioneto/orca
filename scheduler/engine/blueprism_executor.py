"""
Executor de jobs Blue Prism via AutomateC.exe.
Requer Windows; valida presença do executável.
Futuro: integração via API do Blue Prism.
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

AUTOMATEC_NAMES = ["AutomateC.exe", "AutomateC.exe"]


def _find_automatec(executable_path: str = None) -> str:
    """Retorna o caminho do AutomateC.exe. Levanta FileNotFoundError se não encontrar."""
    if executable_path and os.path.isfile(executable_path):
        return executable_path
    if platform.system() != "Windows":
        raise ValueError("Blue Prism só é suportado no Windows.")
    for name in AUTOMATEC_NAMES:
        found = _which_win(name)
        if found:
            return found
    raise FileNotFoundError(
        "AutomateC.exe não encontrado. Instale o Blue Prism ou informe executable_path em executor_config."
    )


def _which_win(executable: str) -> Optional[str]:
    path_env = os.environ.get("PATH", "")
    for folder in path_env.split(os.pathsep):
        full = os.path.join(folder.strip(), executable)
        if os.path.isfile(full):
            return full
    return None


def _fail_result(message: str, duration: float = 0.0) -> Dict[str, Any]:
    return {
        "status": TaskStatus.FAILED,
        "returncode": -1,
        "stdout": "",
        "stderr": message,
        "duration": duration,
        "error_message": message,
    }


class BluePrismJobExecutor(JobExecutor):
    """
    Executa processos Blue Prism via AutomateC.exe.
    executor_config: process_name (obrigatório), user, password, ou sso=True; opcional resource, executable_path.
    """

    def run(self, task: "Task", base_dir: str) -> Dict[str, Any]:
        config = task.executor_config or {}
        process_name = config.get("process_name")
        executable_path = config.get("executable_path")

        if not process_name:
            return _fail_result("executor_config deve conter 'process_name'.")

        if platform.system() != "Windows":
            return _fail_result("Blue Prism só é suportado no Windows.")

        exe = _find_automatec(executable_path)
        # AutomateC /run "Process Name" /user username password  ou  /sso
        cmd = [exe, "/run", process_name]
        if config.get("sso"):
            cmd.append("/sso")
        else:
            user = config.get("user")
            password = config.get("password", "")
            if user:
                cmd.extend(["/user", user, password])
        resource = config.get("resource")
        if resource:
            cmd.extend(["/resource", resource])

        start = datetime.now()
        logger.info("Executando Blue Prism: AutomateC /run ...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=task.timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds()
            return _fail_result(f"Timeout após {task.timeout}s", duration=duration)
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.exception("Erro ao executar Blue Prism: %s", e)
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
