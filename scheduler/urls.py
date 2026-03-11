from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    path('pipelines/', views.PipelineListView.as_view(), name='pipeline_list'),
    path('pipelines/create/', views.PipelineCreateView.as_view(), name='pipeline_create'),
    path('pipelines/<int:pk>/', views.PipelineDetailView.as_view(), name='pipeline_detail'),
    path('pipelines/<int:pk>/run/', views.run_pipeline_now, name='pipeline_run'),
    path('pipelines/<int:pk>/edit/', views.PipelineUpdateView.as_view(), name='pipeline_update'),
    path('pipelines/<int:pk>/delete/', views.PipelineDeleteView.as_view(), name='pipeline_delete'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/run/', views.run_task_now, name='task_run'),
    path('tasks/<int:pk>/cancel/', views.cancel_task_execution, name='task_cancel'),
    path('executions/', views.ExecutionListView.as_view(), name='execution_list'),
    path('executions/export/', views.execution_export, name='execution_export'),
    path('executions/status/', views.execution_status_api, name='execution_status_api'),
    path('executions/<int:pk>/', views.ExecutionDetailView.as_view(), name='execution_detail'),
    path('executions/<int:pk>/status/', views.execution_detail_status_api, name='execution_detail_status_api'),
    path('executions/<int:pk>/cancel/', views.cancel_execution, name='execution_cancel'),
    path('pipelines/<int:pk>/status/', views.pipeline_status_api, name='pipeline_status_api'),
    path('dashboard/executions/', views.dashboard_executions_api, name='dashboard_executions_api'),
    path('reload/', views.reload_scheduler, name='reload'),
]

