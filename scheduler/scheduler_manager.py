"""
Gerenciador do APScheduler com executor não-bloqueante.

Execução assíncrona / paralela:
- Agendamento: até 20 tarefas podem rodar ao mesmo tempo (ThreadPoolExecutor com 20 threads).
- "Executar tarefa" na interface: cada clique dispara uma thread; várias tarefas podem rodar em paralelo.
- "Executar pipeline": cada camada do DAG roda em paralelo (uma thread por tarefa na camada);
  só avança para a próxima camada quando todas da camada atual terminarem.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from django.conf import settings
from .models import Pipeline, Task, TaskStatus, ScheduleType
from .dag_manager import DAGManager
from .engine import run_task as engine_run_task
import threading

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Gerenciador central do scheduler"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.scheduler = None
        self.dag_manager = DAGManager()
        self.is_running = False
    
    def start(self):
        """Inicia o scheduler"""
        if self.is_running:
            logger.warning("Scheduler já está rodando")
            return
        
        # Configura executor com pool de threads (não-bloqueante)
        executors = {
            'default': ThreadPoolExecutor(20),  # 20 threads paralelas
        }
        
        jobstores = {
            'default': MemoryJobStore()
        }
        
        job_defaults = {
            'coalesce': True,  # Agrupa execuções perdidas
            'max_instances': 3,  # Máximo de instâncias simultâneas por job
            'misfire_grace_time': 300  # 5 minutos de tolerância
        }
        
        self.scheduler = BackgroundScheduler(
            executors=executors,
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone=timezone(settings.TIME_ZONE)
        )
        
        self.scheduler.start()
        self.is_running = True
        
        # Carrega pipelines ativos
        self.reload_all_pipelines()
        
        logger.info("Scheduler iniciado com sucesso")
    
    def stop(self):
        """Para o scheduler"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler parado")
    
    def reload_all_pipelines(self):
        """Recarrega todos os pipelines ativos"""
        if not self.is_running:
            return
        
        # Remove todos os jobs existentes
        self.scheduler.remove_all_jobs()
        
        # Carrega pipelines ativos
        pipelines = Pipeline.objects.filter(is_active=True)
        
        for pipeline in pipelines:
            self.schedule_pipeline(pipeline)
        
        logger.info(f"Recarregados {pipelines.count()} pipelines")
    
    def schedule_pipeline(self, pipeline: Pipeline):
        """Agenda um pipeline"""
        if not self.is_running:
            return
        
        tasks = pipeline.tasks.filter(is_active=True).order_by('name')
        
        for task in tasks:
            self.schedule_task(task)
    
    def schedule_task(self, task: Task):
        """Agenda uma tarefa individual. Tarefas com dependências não são agendadas por cron: rodam após as dependências."""
        if not self.is_running:
            return
        
        if task.depends_on.filter(is_active=True).exists():
            logger.info(f"Tarefa {task.name} não agendada por cron (será executada após as dependências concluírem)")
            return

        job_id = f"task_{task.id}"
        
        # Remove job existente se houver
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
        
        # Cria trigger baseado no tipo de agendamento
        trigger = self._create_trigger(task)
        
        if not trigger:
            logger.warning(f"Não foi possível criar trigger para tarefa {task.id}")
            return
        
        # Adiciona job
        self.scheduler.add_job(
            self._execute_task_wrapper,
            trigger=trigger,
            id=job_id,
            name=f"{task.pipeline.name} - {task.name}",
            args=[task.id],
            replace_existing=True
        )
        
        logger.info(f"Tarefa {task.name} agendada (ID: {job_id})")
    
    def get_next_run_time(self, task_id: int):
        """Retorna o datetime da próxima execução da tarefa, ou None se não agendada."""
        if not self.is_running or not self.scheduler:
            return None
        job_id = f"task_{task_id}"
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                return job.next_run_time
            return None
        except Exception:
            return None
    
    def _create_trigger(self, task: Task):
        """Cria trigger baseado na configuração da tarefa"""
        schedule_type = task.schedule_type
        config = task.schedule_config or {}
        tz = timezone(settings.TIME_ZONE)
        
        if schedule_type == ScheduleType.INTERVAL:
            # Intervalo simples
            if 'seconds' in config:
                return IntervalTrigger(seconds=config['seconds'], timezone=tz)
            elif 'minutes' in config:
                return IntervalTrigger(minutes=config['minutes'], timezone=tz)
            elif 'hours' in config:
                return IntervalTrigger(hours=config['hours'], timezone=tz)
            elif 'days' in config:
                return IntervalTrigger(days=config['days'], timezone=tz)
        
        elif schedule_type == ScheduleType.CRON:
            # Cron expression
            return CronTrigger(
                year=config.get('year'),
                month=config.get('month'),
                day=config.get('day'),
                week=config.get('week'),
                day_of_week=config.get('day_of_week'),
                hour=config.get('hour'),
                minute=config.get('minute'),
                second=config.get('second'),
                timezone=tz
            )
        
        elif schedule_type == ScheduleType.DAILY:
            # Diário em horário específico
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(hour=hour, minute=minute, timezone=tz)
        
        elif schedule_type == ScheduleType.WEEKLY:
            # Semanal - dia específico da semana
            day_of_week = config.get('day_of_week', 0)  # 0=segunda, 6=domingo
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=tz)
        
        elif schedule_type == ScheduleType.BIWEEKLY:
            # Quinzenal - a cada 2 semanas
            day_of_week = config.get('day_of_week', 0)
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            # Implementação: executa no dia da semana especificado, a cada 2 semanas
            # Usa week='*/2' no cron
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, week='*/2', timezone=tz)
        
        elif schedule_type == ScheduleType.MONTHLY:
            # Mensal - dia específico do mês
            day = config.get('day', 1)
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(day=day, hour=hour, minute=minute, timezone=tz)
        
        # Default: diário à meia-noite
        return CronTrigger(hour=0, minute=0, timezone=tz)
    
    def _execute_task_wrapper(self, task_id: int):
        """Wrapper para executar tarefa (chamado pelo scheduler)"""
        try:
            task = Task.objects.get(id=task_id)
            self._execute_task(task)
        except Task.DoesNotExist:
            logger.error(f"Tarefa {task_id} não encontrada")
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task_id}: {e}")
    
    def _execute_task(self, task: Task):
        """Executa uma tarefa com verificação de dependências. Criação e atualização da execução ficam no engine."""
        if not self.dag_manager.can_execute(task):
            logger.info(f"Tarefa {task.name} aguardando dependências")
            return

        result = engine_run_task(task)
        logger.info("Tarefa %s executada: %s", task.name, result.get("status", "?"))

        if result.get("status") == TaskStatus.SUCCESS:
            self._trigger_dependent_tasks(task)

    def _trigger_dependent_tasks(self, task: Task):
        """Dispara as tarefas que dependem desta, assim que esta termina com sucesso."""
        for dep in task.dependents.filter(is_active=True):
            if self.dag_manager.can_execute(dep):
                logger.info("Disparando tarefa dependente: %s (após %s)", dep.name, task.name)
                threading.Thread(target=self._execute_task, args=(dep,), daemon=True).start()

