"""
Core Engine: JobRunner – lock, retry, timeout e delegação ao executor.
"""
import logging
import time
from typing import Any, Dict

from django.conf import settings
from django.utils import timezone

from ..models import Task, TaskExecution, TaskStatus
from .factory import get_job_executor

logger = logging.getLogger(__name__)

# Tempo além do qual uma execução RUNNING é considerada travada (segundos)
# Se a tarefa não tiver timeout, execuções “penduradas” (processo morto) são liberadas após esse tempo
STALE_RUNNING_SECONDS = 900  # 15 minutos


def release_stale_locks(task: Task) -> int:
    """
    Marca como FAILED execuções RUNNING desta tarefa que passaram do tempo razoável
    (timeout da tarefa * 2, ou 5 min se não houver timeout). Também libera RUNNING com started_at nulo.
    """
    from datetime import timedelta
    from django.db.models import Q

    now = timezone.now()
    stale_seconds = (task.timeout or 0) * 2 if task.timeout else STALE_RUNNING_SECONDS
    limit = now - timedelta(seconds=stale_seconds)

    stuck = TaskExecution.objects.filter(
        task_id=task.id,
        status=TaskStatus.RUNNING,
    ).filter(Q(started_at__lt=limit) | Q(started_at__isnull=True))
    count = stuck.count()
    if count:
        stuck.update(
            status=TaskStatus.FAILED,
            finished_at=now,
            error_message="Execução considerada travada (timeout ou processo interrompido).",
        )
        logger.warning(
            "Tarefa %s (%s): %s execução(ões) RUNNING travada(s) marcada(s) como FAILED.",
            task.name,
            task.id,
            count,
        )
    return count


def is_task_locked(task: Task) -> bool:
    """
    Verifica se já existe execução RUNNING para esta tarefa (evita duplicidade).
    """
    return TaskExecution.objects.filter(
        task_id=task.id,
        status=TaskStatus.RUNNING,
    ).exists()


def run_task(task: Task) -> Dict[str, Any]:
    """
    Executa uma tarefa via Core Engine: verifica lock, cria TaskExecution (RUNNING),
    roda o executor, atualiza a execução e retorna o resultado.
    Retorna dict com status, returncode, stdout, stderr, duration, error_message.
    """
    release_stale_locks(task)
    if is_task_locked(task):
        logger.warning("Tarefa %s (%s) já está em execução; ignorando nova execução.", task.name, task.id)
        return {
            "status": TaskStatus.FAILED,
            "returncode": -1,
            "stdout": "",
            "stderr": "Job já em execução (lock).",
            "duration": 0.0,
            "error_message": "Job já em execução (lock).",
        }

    execution = TaskExecution.objects.create(
        task=task,
        pipeline=task.pipeline,
        status=TaskStatus.RUNNING,
        started_at=timezone.now(),
    )

    executor = get_job_executor(task.executor_type)
    base_dir = getattr(settings, "BASE_DIR", "") or ""

    retry_count = 0
    last_result = None

    try:
        while retry_count <= (task.retries or 0):
            last_result = executor.run(task, base_dir)
            if last_result.get("status") == TaskStatus.SUCCESS:
                last_result["retry_count"] = retry_count
                execution.status = last_result["status"]
                execution.finished_at = timezone.now()
                execution.returncode = last_result.get("returncode")
                execution.stdout = last_result.get("stdout", "") or ""
                execution.stderr = last_result.get("stderr", "") or ""
                execution.error_message = last_result.get("error_message", "") or ""
                execution.duration = last_result.get("duration")
                execution.retry_count = last_result.get("retry_count", 0)
                execution.save()
                return last_result
            retry_count += 1
            if retry_count <= (task.retries or 0):
                delay = task.retry_delay or 60
                logger.warning(
                    "Tarefa %s falhou, tentativa %s/%s; aguardando %ss.",
                    task.name,
                    retry_count,
                    task.retries,
                    delay,
                )
                time.sleep(delay)

        if last_result is not None:
            last_result["retry_count"] = retry_count
            execution.status = last_result["status"]
            execution.finished_at = timezone.now()
            execution.returncode = last_result.get("returncode")
            execution.stdout = last_result.get("stdout", "") or ""
            execution.stderr = last_result.get("stderr", "") or ""
            execution.error_message = last_result.get("error_message", "") or ""
            execution.duration = last_result.get("duration")
            execution.retry_count = retry_count
            execution.save()
            return last_result

        failed_result = {
            "status": TaskStatus.FAILED,
            "returncode": -1,
            "stdout": "",
            "stderr": "Nenhum resultado retornado.",
            "duration": 0.0,
            "error_message": "Nenhum resultado retornado.",
            "retry_count": retry_count,
        }
        execution.status = TaskStatus.FAILED
        execution.finished_at = timezone.now()
        execution.error_message = failed_result["error_message"]
        execution.save()
        return failed_result

    except Exception as e:
        execution.status = TaskStatus.FAILED
        execution.finished_at = timezone.now()
        execution.error_message = str(e)
        execution.save()
        logger.exception("Erro ao executar tarefa %s: %s", task.name, e)
        return {
            "status": TaskStatus.FAILED,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": 0.0,
            "error_message": str(e),
        }
