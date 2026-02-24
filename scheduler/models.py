from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ScriptType(models.TextChoices):
    PYTHON = 'python', 'Python (.py)'
    SHELL = 'shell', 'Shell (.sh)'
    BATCH = 'batch', 'Batch (.bat)'
    POWERSHELL = 'powershell', 'PowerShell (.ps1)'
    NODE = 'node', 'Node.js (.js)'
    PERL = 'perl', 'Perl (.pl)'
    RUBY = 'ruby', 'Ruby (.rb)'
    GO = 'go', 'Go (.go)'


class ScheduleType(models.TextChoices):
    INTERVAL = 'interval', 'Intervalo'
    CRON = 'cron', 'Cron'
    WEEKLY = 'weekly', 'Semanal'
    MONTHLY = 'monthly', 'Mensal'
    BIWEEKLY = 'biweekly', 'Quinzenal'
    DAILY = 'daily', 'Diário'


class TaskStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    RUNNING = 'running', 'Em Execução'
    SUCCESS = 'success', 'Sucesso'
    FAILED = 'failed', 'Falhou'
    RETRY = 'retry', 'Retentativa'


class Pipeline(models.Model):
    """Pipeline/DAG de tarefas"""
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pipelines')
    
    class Meta:
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ExecutorType(models.TextChoices):
    """Tipo de executor: script local ou RPA."""
    SCRIPT = 'script', 'Script (.py, .ps1, ...)'
    UIPATH = 'uipath', 'UiPath'
    BLUEPRISM = 'blueprism', 'Blue Prism'


class Task(models.Model):
    """Tarefa individual"""
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='tasks', verbose_name='Pipeline')
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    # Executor: script (padrão) ou RPA
    executor_type = models.CharField(
        max_length=20,
        choices=ExecutorType.choices,
        default=ExecutorType.SCRIPT,
        verbose_name='Tipo de Executor',
    )
    executor_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configuração do Executor (RPA)',
        help_text='Para UiPath: process_file, executable_path. Para Blue Prism: process_name, user, password ou sso.',
    )
    # Script (usado quando executor_type=script)
    script_path = models.CharField(max_length=500, blank=True, verbose_name='Caminho do Script')
    script_type = models.CharField(max_length=20, choices=ScriptType.choices, default=ScriptType.PYTHON, verbose_name='Tipo de Script')
    script_interpreter_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Interpretador (ex: /venv/bin/python)',
        help_text='Opcional. Caminho do Python/interpretador do ambiente do usuário. Em branco usa o do sistema (PATH). Ex: /app/venv/bin/python',
    )
    
    # Dependências
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents', verbose_name='Depende de')
    
    # Configurações de execução
    retries = models.IntegerField(default=0, verbose_name='Tentativas')
    retry_delay = models.IntegerField(default=60, verbose_name='Delay entre Tentativas (segundos)')
    timeout = models.IntegerField(null=True, blank=True, verbose_name='Timeout (segundos)')
    
    # Agendamento
    schedule_type = models.CharField(max_length=20, choices=ScheduleType.choices, default=ScheduleType.DAILY, verbose_name='Tipo de Agendamento')
    schedule_config = models.JSONField(default=dict, verbose_name='Configuração do Agendamento')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Metadados
    order = models.IntegerField(default=0, verbose_name='Ordem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['pipeline', 'name']
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"
    
    def get_dependencies(self):
        """Retorna IDs das tarefas das quais depende"""
        return list(self.depends_on.values_list('id', flat=True))

    def get_schedule_display(self):
        """
        Retorna descrição legível do agendamento a partir do JSON (schedule_config).
        Ex: {"minutes": 30} -> "Execução a cada 30 minutos"
        """
        config = self.schedule_config or {}
        if not isinstance(config, dict):
            return "Sem agendamento definido"
        st = self.schedule_type
        # Intervalo
        if st == ScheduleType.INTERVAL:
            if 'seconds' in config:
                n = config['seconds']
                return f"Execução a cada {n} segundo{'s' if n != 1 else ''}"
            if 'minutes' in config:
                n = config['minutes']
                return f"Execução a cada {n} minuto{'s' if n != 1 else ''}"
            if 'hours' in config:
                n = config['hours']
                return f"Execução a cada {n} hora{'s' if n != 1 else ''}"
            if 'days' in config:
                n = config['days']
                return f"Execução a cada {n} dia{'s' if n != 1 else ''}"
            return "Intervalo (config inválido)"
        # Diário
        if st == ScheduleType.DAILY:
            h = config.get('hour', 0)
            m = config.get('minute', 0)
            return f"Execução diária às {h:02d}:{m:02d}"
        # Semanal
        if st == ScheduleType.WEEKLY:
            dias = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
            dow = config.get('day_of_week', 0)
            dia = dias[dow] if 0 <= dow <= 6 else str(dow)
            h = config.get('hour', 0)
            m = config.get('minute', 0)
            return f"Execução semanal ({dia}) às {h:02d}:{m:02d}"
        # Mensal
        if st == ScheduleType.MONTHLY:
            day = config.get('day', 1)
            h = config.get('hour', 0)
            m = config.get('minute', 0)
            return f"Execução mensal (dia {day}) às {h:02d}:{m:02d}"
        # Quinzenal
        if st == ScheduleType.BIWEEKLY:
            dias = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
            dow = config.get('day_of_week', 0)
            dia = dias[dow] if 0 <= dow <= 6 else str(dow)
            h = config.get('hour', 0)
            m = config.get('minute', 0)
            return f"Execução quinzenal ({dia}) às {h:02d}:{m:02d}"
        # Cron
        if st == ScheduleType.CRON:
            parts = []
            if 'minute' in config:
                parts.append(f"min {config['minute']}")
            if 'hour' in config:
                parts.append(f"h {config['hour']}")
            if 'day' in config:
                parts.append(f"dia {config['day']}")
            if 'month' in config:
                parts.append(f"mês {config['month']}")
            if 'day_of_week' in config:
                parts.append(f"dia_semana {config['day_of_week']}")
            if parts:
                return "Execução (cron): " + ", ".join(parts)
            return "Execução (cron)"
        return self.get_schedule_type_display() or "Agendamento"


class TaskExecution(models.Model):
    """Histórico de execuções de tarefas"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='executions', verbose_name='Tarefa')
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='executions', verbose_name='Pipeline')
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING, verbose_name='Status')
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Iniciado em')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='Finalizado em')
    duration = models.FloatField(null=True, blank=True, verbose_name='Duração (segundos)')
    
    returncode = models.IntegerField(null=True, blank=True, verbose_name='Código de Retorno')
    stdout = models.TextField(blank=True, verbose_name='Saída Padrão')
    stderr = models.TextField(blank=True, verbose_name='Erro')
    
    retry_count = models.IntegerField(default=0, verbose_name='Tentativa')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Execução'
        verbose_name_plural = 'Execuções'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['task', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.task.name} - {self.status} - {self.created_at}"
    
    def calculate_duration(self):
        """Calcula duração da execução"""
        if self.started_at and self.finished_at:
            self.duration = (self.finished_at - self.started_at).total_seconds()
            self.save(update_fields=['duration'])

