from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Pipeline, Task, TaskExecution, TaskStatus
from .forms import PipelineForm, TaskForm
from .scheduler_manager import SchedulerManager
from .dag_manager import DAGManager
from .utils import infer_schedule_type
import json
import threading

# Views de Pipeline

class PipelineListView(ListView):
    model = Pipeline
    template_name = 'scheduler/pipeline_list.html'
    context_object_name = 'pipelines'
    paginate_by = 20
    
    def get_queryset(self):
        return Pipeline.objects.all().prefetch_related('tasks')


class PipelineDetailView(DetailView):
    model = Pipeline
    template_name = 'scheduler/pipeline_detail.html'
    context_object_name = 'pipeline'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = list(self.object.tasks.all().order_by('name'))
        scheduler = SchedulerManager()
        for task in tasks:
            task.next_run_time_dt = scheduler.get_next_run_time(task.id)
        running_task_ids = set(
            TaskExecution.objects.filter(
                task__pipeline=self.object,
                status=TaskStatus.RUNNING,
            ).values_list('task_id', flat=True)
        )
        for task in tasks:
            task.has_running_execution = task.id in running_task_ids
        context['tasks'] = tasks
        context['executions'] = TaskExecution.objects.filter(
            pipeline=self.object
        ).order_by('-created_at')[:10]
        # Camadas de execução (DAG): cada camada pode rodar em paralelo
        try:
            dag = DAGManager()
            context['execution_layers'] = dag.get_execution_order(self.object.id)
        except Exception:
            context['execution_layers'] = [[t] for t in tasks] if tasks else []
        # Último status de execução por tarefa (para o gráfico)
        latest_exec_ids = TaskExecution.objects.filter(
            pipeline=self.object
        ).values('task_id').annotate(max_id=Max('id')).values_list('max_id', flat=True)
        last_executions = TaskExecution.objects.filter(
            id__in=latest_exec_ids
        ).values('task_id', 'status')
        execution_status_by_task = {e['task_id']: e['status'] for e in last_executions}
        context['execution_status_by_task'] = execution_status_by_task
        # Camadas com (task, status) para o template do gráfico
        execution_layers = context.get('execution_layers', [])
        context['execution_layers_with_status'] = [
            [{'task': t, 'status': execution_status_by_task.get(t.id, 'pending')} for t in layer]
            for layer in execution_layers
        ]
        return context


class PipelineCreateView(CreateView):
    model = Pipeline
    form_class = PipelineForm
    template_name = 'scheduler/pipeline_form.html'
    success_url = reverse_lazy('scheduler:pipeline_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Pipeline "{self.object.name}" criado com sucesso!')
        return response


class PipelineUpdateView(UpdateView):
    model = Pipeline
    form_class = PipelineForm
    template_name = 'scheduler/pipeline_form.html'
    success_url = reverse_lazy('scheduler:pipeline_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Pipeline "{self.object.name}" atualizado com sucesso!')
        # Recarrega scheduler se pipeline foi ativado/desativado
        scheduler = SchedulerManager()
        scheduler.reload_all_pipelines()
        return response


class PipelineDeleteView(DeleteView):
    model = Pipeline
    template_name = 'scheduler/pipeline_confirm_delete.html'
    success_url = reverse_lazy('scheduler:pipeline_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'Pipeline deletado com sucesso!')
        scheduler = SchedulerManager()
        scheduler.reload_all_pipelines()
        return response


# Views de Task

class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'scheduler/task_form.html'
    
    def get_success_url(self):
        return reverse_lazy('scheduler:pipeline_detail', kwargs={'pk': self.object.pipeline.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_pipeline_id'] = self.request.GET.get('pipeline')
        return context
    
    def form_valid(self, form):
        pipeline_id = self.request.GET.get('pipeline') or (form.cleaned_data.get('pipeline') and form.cleaned_data['pipeline'].id)
        if pipeline_id:
            form.instance.pipeline_id = pipeline_id
        form.instance.schedule_type = infer_schedule_type(form.cleaned_data['schedule_config'])
        super().form_valid(form)
        messages.success(self.request, f'Tarefa "{self.object.name}" criada com sucesso!')
        scheduler = SchedulerManager()
        scheduler.schedule_pipeline(self.object.pipeline)
        return redirect('scheduler:pipeline_detail', pk=self.object.pipeline_id)


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'scheduler/task_form.html'
    
    def get_success_url(self):
        return reverse_lazy('scheduler:pipeline_detail', kwargs={'pk': self.object.pipeline.id})
    
    def form_valid(self, form):
        form.instance.schedule_type = infer_schedule_type(form.cleaned_data['schedule_config'])
        super().form_valid(form)
        messages.success(self.request, f'Tarefa "{self.object.name}" atualizada com sucesso!')
        scheduler = SchedulerManager()
        scheduler.schedule_pipeline(self.object.pipeline)
        return redirect('scheduler:pipeline_detail', pk=self.object.pipeline_id)


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'scheduler/task_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('scheduler:pipeline_detail', kwargs={'pk': self.object.pipeline.id})
    
    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        pipeline = task.pipeline
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'Tarefa deletada com sucesso!')
        scheduler = SchedulerManager()
        scheduler.schedule_pipeline(pipeline)
        return response


# Views de Execution

# Tempo (segundos) após o qual uma execução RUNNING é considerada travada e liberada ao abrir a lista
# Só consideramos pelo started_at (e nulo); 15 min evita matar tarefas que demoram um pouco
STALE_EXECUTION_SECONDS = 900  # 15 minutos


def release_all_stale_executions():
    """
    Marca como FAILED apenas execuções RUNNING realmente travadas:
    started_at nulo (processo morreu antes de registrar) ou started_at há mais de 15 min.
    Não usa created_at para não marcar execuções legítimas como falha.
    Retorna quantas foram atualizadas.
    """
    from datetime import timedelta
    from django.db.models import Q
    now = timezone.now()
    limit = now - timedelta(seconds=STALE_EXECUTION_SECONDS)
    stuck = TaskExecution.objects.filter(
        status=TaskStatus.RUNNING,
    ).filter(Q(started_at__lt=limit) | Q(started_at__isnull=True))
    count = stuck.count()
    if count:
        stuck.update(
            status=TaskStatus.FAILED,
            finished_at=now,
            error_message="Execução considerada travada (processo interrompido ou timeout).",
        )
    return count


class ExecutionListView(ListView):
    model = TaskExecution
    template_name = 'scheduler/execution_list.html'
    context_object_name = 'executions'
    paginate_by = 50
    
    def get_queryset(self):
        # Libera execuções travadas ao abrir a página (para desbloquear tarefas)
        released = release_all_stale_executions()
        if released:
            messages.success(
                self.request,
                f'{released} execução(ões) travada(s) foram marcadas como falha. Você já pode executar as tarefas novamente.',
            )
        queryset = TaskExecution.objects.select_related('task', 'pipeline').all()
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        pipeline_id = self.request.GET.get('pipeline')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        task_id = self.request.GET.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        from datetime import timedelta
        context = super().get_context_data(**kwargs)
        # IDs de execuções RUNNING consideradas travadas (mais de 15 min sem concluir)
        limit = timezone.now() - timedelta(seconds=STALE_EXECUTION_SECONDS)
        from django.db.models import Q
        context['stale_execution_ids'] = set(
            TaskExecution.objects.filter(
                status=TaskStatus.RUNNING,
            ).filter(Q(started_at__lt=limit) | Q(started_at__isnull=True)).values_list('id', flat=True)
        )
        return context


class ExecutionDetailView(DetailView):
    model = TaskExecution
    template_name = 'scheduler/execution_detail.html'
    context_object_name = 'execution'


@login_required
@require_http_methods(["POST"])
def cancel_execution(request, pk):
    """Cancela uma execução em andamento (marca como FAILED). Redireciona para a lista de execuções."""
    execution = get_object_or_404(TaskExecution, pk=pk)
    if execution.status != TaskStatus.RUNNING:
        messages.info(request, 'Essa execução já não está em andamento.')
        return redirect('scheduler:execution_list')
    execution.status = TaskStatus.FAILED
    execution.finished_at = timezone.now()
    execution.error_message = 'Cancelado pelo usuário.'
    execution.save()
    messages.success(request, f'Execução de "{execution.task.name}" cancelada.')
    return redirect('scheduler:execution_list')


@login_required
@require_http_methods(["POST"])
def reload_scheduler(request):
    """Recarrega todos os pipelines no scheduler"""
    try:
        scheduler = SchedulerManager()
        scheduler.reload_all_pipelines()
        messages.success(request, 'Scheduler recarregado com sucesso!')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        messages.error(request, f'Erro ao recarregar scheduler: {e}')
        return JsonResponse({'status': 'error', 'message': str(e)})


def _run_task_in_background(task_id: int):
    """Executa uma tarefa em background (thread)."""
    try:
        task = Task.objects.get(id=task_id)
        scheduler = SchedulerManager()
        scheduler._execute_task(task)
    except Exception:
        pass  # Erros já são logados no scheduler


@login_required
@require_http_methods(["POST"])
def run_task_now(request, pk):
    """Dispara execução manual da tarefa: encerra qualquer execução em andamento dessa tarefa e inicia a nova."""
    task = get_object_or_404(Task, pk=pk)
    TaskExecution.objects.filter(
        task_id=task.id,
        status=TaskStatus.RUNNING,
    ).update(
        status=TaskStatus.FAILED,
        finished_at=timezone.now(),
        error_message='Cancelado para nova execução (usuário clicou em Executar).',
    )
    threading.Thread(target=_run_task_in_background, args=(task.id,), daemon=True).start()
    messages.success(request, f'Execução da tarefa "{task.name}" iniciada. Acompanhe em Execuções.')
    return redirect('scheduler:pipeline_detail', pk=task.pipeline_id)


@login_required
@require_http_methods(["POST"])
def cancel_task_execution(request, pk):
    """Cancela execuções RUNNING da tarefa (marca como FAILED). Próxima execução só no agendamento ou ao clicar em Play."""
    task = get_object_or_404(Task, pk=pk)
    cancelled = TaskExecution.objects.filter(
        task_id=task.id,
        status=TaskStatus.RUNNING,
    ).update(
        status=TaskStatus.FAILED,
        finished_at=timezone.now(),
        error_message='Cancelado pelo usuário.',
    )
    if cancelled:
        messages.success(request, f'Execução da tarefa "{task.name}" cancelada. Ela voltará a rodar no próximo agendamento ou ao clicar em Play.')
    else:
        messages.info(request, f'Tarefa "{task.name}" não tinha execução em andamento.')
    return redirect('scheduler:pipeline_detail', pk=task.pipeline_id)


def _run_pipeline_in_background(pipeline_id: int):
    """
    Executa todas as tarefas do pipeline em background:
    sem dependências = todas na mesma camada (em paralelo); com dependências = por camadas do DAG.
    Dentro de cada camada, as tarefas rodam em paralelo (uma thread por tarefa).
    Antes de rodar, encerra qualquer execução RUNNING das tarefas deste pipeline (para nova execução).
    """
    try:
        pipeline = Pipeline.objects.get(id=pipeline_id)
        task_ids = list(pipeline.tasks.values_list('id', flat=True))
        if task_ids:
            TaskExecution.objects.filter(
                task_id__in=task_ids,
                status=TaskStatus.RUNNING,
            ).update(
                status=TaskStatus.FAILED,
                finished_at=timezone.now(),
                error_message='Cancelado para nova execução do pipeline (usuário clicou em Executar).',
            )
        dag = DAGManager()
        scheduler = SchedulerManager()
        layers = dag.get_execution_order(pipeline_id)
        for layer in layers:
            tasks_to_run = [t for t in sorted(layer, key=lambda t: t.name) if t.is_active]
            if not tasks_to_run:
                continue
            threads = [
                threading.Thread(target=scheduler._execute_task, args=(task,), daemon=True)
                for task in tasks_to_run
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
    except Exception:
        pass  # Erros já são logados no scheduler


@login_required
@require_http_methods(["POST"])
def run_pipeline_now(request, pk):
    """Dispara execução manual do pipeline (todas as tarefas na ordem estipulada)."""
    pipeline = get_object_or_404(Pipeline, pk=pk)
    threading.Thread(target=_run_pipeline_in_background, args=(pipeline.id,), daemon=True).start()
    messages.success(
        request,
        f'Execução do pipeline "{pipeline.name}" iniciada (por dependências). Acompanhe em Execuções.'
    )
    return redirect('scheduler:pipeline_list')

