"""
Classe base para todos os executores de script do Orca.
"""
import os
import shutil
import subprocess
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ..models import TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Resultado padronizado da execução de um script."""
    status: str  # TaskStatus.SUCCESS ou TaskStatus.FAILED
    returncode: int
    stdout: str
    stderr: str
    duration: float
    started_at: datetime
    finished_at: datetime
    error_message: str = ""
    script_path: str = ""
    script_type: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error_message": self.stderr if self.returncode != 0 else self.error_message,
        }


class BaseExecutor(ABC):
    """
    Executor base: subprocess, captura stdout/stderr, exit code.
    Cada tipo de script implementa get_command() e validações de SO/interpretador.
    """

    # Extensões suportadas por este executor (ex: ['.py'])
    extensions: List[str] = []
    # Nome do interpretador para validação no PATH (ex: 'python3')
    interpreter_name: Optional[str] = None
    # SO permitido: 'windows', 'linux', 'darwin' (macOS), ou None = todos
    allowed_os: Optional[List[str]] = None

    def __init__(self):
        self._platform = None

    @property
    def platform(self) -> str:
        if self._platform is None:
            import platform
            self._platform = platform.system().lower()  # 'windows', 'linux', 'darwin'
        return self._platform

    def validate_os(self) -> None:
        """Levanta ValueError se o script não for compatível com o SO atual."""
        if self.allowed_os is None:
            return
        if self.platform not in self.allowed_os:
            raise ValueError(
                f"Script incompatível com o sistema atual ({self.platform}). "
                f"Tipos permitidos neste SO: {', '.join(self.allowed_os)}."
            )

    def validate_interpreter(self, interpreter_path: Optional[str] = None) -> None:
        """
        Valida se o interpretador existe (PATH ou caminho explícito).
        Levanta FileNotFoundError se não encontrar.
        """
        if interpreter_path:
            if not os.path.isfile(interpreter_path) and not shutil.which(interpreter_path):
                raise FileNotFoundError(f"Interpretador não encontrado: {interpreter_path}")
            return
        if self.interpreter_name and not shutil.which(self.interpreter_name):
            raise FileNotFoundError(
                f"Interpretador '{self.interpreter_name}' não encontrado no PATH. "
                "Instale-o ou informe o caminho completo no campo interpretador."
            )

    @abstractmethod
    def get_command(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> List[str]:
        """Retorna a lista de argumentos para subprocess (comando + argumentos)."""
        pass

    def resolve_script_path(self, script_path: str, base_dir: Optional[str] = None) -> str:
        """Resolve path absoluto e fallback para scripts/<nome> se path absoluto não existir."""
        if base_dir and not os.path.isabs(script_path):
            script_path = os.path.normpath(os.path.join(base_dir, script_path))
        if not os.path.exists(script_path) and base_dir and os.path.isabs(script_path):
            nome = os.path.basename(script_path)
            fallback = os.path.join(base_dir, "scripts", nome)
            if os.path.exists(fallback):
                logger.info("Usando script em scripts/%s (caminho original não existe)", nome)
                return fallback
        return script_path

    def execute(
        self,
        script_path: str,
        timeout: Optional[int] = None,
        base_dir: Optional[str] = None,
        args: Optional[List[str]] = None,
        interpreter_path: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Executa o script via subprocess. Captura stdout/stderr e retorna ExecutionResult.
        Não lança exceção em exit code != 0; o resultado indica status FAILED.
        """
        args = args or []
        script_path = self.resolve_script_path(script_path, base_dir)
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script não encontrado: {script_path}")

        self.validate_os()
        self.validate_interpreter(interpreter_path)

        cmd = self.get_command(script_path, args=args, interpreter_path=interpreter_path)
        cwd = os.path.dirname(script_path) if os.path.dirname(script_path) else None
        start_time = datetime.now()

        logger.info(
            "Executando script type=%s path=%s cmd=%s",
            getattr(self, "script_type_id", "?"),
            script_path,
            cmd,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = f"Timeout após {timeout}s"
            logger.error("Timeout executando %s: %s", script_path, error_msg)
            return ExecutionResult(
                status=TaskStatus.FAILED,
                returncode=-1,
                stdout="",
                stderr=error_msg,
                duration=duration,
                started_at=start_time,
                finished_at=end_time,
                error_message=error_msg,
                script_path=script_path,
                script_type=getattr(self, "script_type_id", ""),
            )
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            logger.exception("Erro executando %s: %s", script_path, error_msg)
            return ExecutionResult(
                status=TaskStatus.FAILED,
                returncode=-1,
                stdout="",
                stderr=error_msg,
                duration=duration,
                started_at=start_time,
                finished_at=end_time,
                error_message=error_msg,
                script_path=script_path,
                script_type=getattr(self, "script_type_id", ""),
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        status = TaskStatus.SUCCESS if result.returncode == 0 else TaskStatus.FAILED

        logger.info(
            "Script finalizado path=%s returncode=%s duration=%.2fs",
            script_path,
            result.returncode,
            duration,
        )

        return ExecutionResult(
            status=status,
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            duration=duration,
            started_at=start_time,
            finished_at=end_time,
            error_message=result.stderr if result.returncode != 0 else "",
            script_path=script_path,
            script_type=getattr(self, "script_type_id", ""),
        )
