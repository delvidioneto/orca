from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.utils import timezone
from scheduler.models import Pipeline, Task, TaskExecution, TaskStatus
from django.db.models import Count, Q
from datetime import timedelta


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        context['total_pipelines'] = Pipeline.objects.count()
        context['active_pipelines'] = Pipeline.objects.filter(is_active=True).count()
        context['total_tasks'] = Task.objects.count()
        context['active_tasks'] = Task.objects.filter(is_active=True).count()
        
        # Execuções recentes
        context['recent_executions'] = TaskExecution.objects.select_related(
            'task', 'pipeline'
        ).order_by('-created_at')[:10]
        
        # Estatísticas de execuções (últimas 24h)
        last_24h = timezone.now() - timedelta(hours=24)
        executions_24h = TaskExecution.objects.filter(created_at__gte=last_24h)
        
        context['executions_24h'] = executions_24h.count()
        context['success_24h'] = executions_24h.filter(status=TaskStatus.SUCCESS).count()
        context['failed_24h'] = executions_24h.filter(status=TaskStatus.FAILED).count()
        context['running_24h'] = executions_24h.filter(status=TaskStatus.RUNNING).count()
        
        # Status por pipeline
        context['pipeline_stats'] = Pipeline.objects.annotate(
            total_tasks=Count('tasks'),
            active_tasks=Count('tasks', filter=Q(tasks__is_active=True))
        )[:10]
        
        # Tarefas com mais falhas (últimas 24h)
        context['failed_tasks'] = TaskExecution.objects.filter(
            created_at__gte=last_24h,
            status=TaskStatus.FAILED
        ).values('task__name', 'task__pipeline__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return context

