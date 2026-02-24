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
    path('executions/<int:pk>/', views.ExecutionDetailView.as_view(), name='execution_detail'),
    path('executions/<int:pk>/cancel/', views.cancel_execution, name='execution_cancel'),
    path('reload/', views.reload_scheduler, name='reload'),
]

