"""
Gerenciador de DAGs (Directed Acyclic Graphs) para dependências entre tarefas
"""
import networkx as nx
from typing import List, Set
from django.db import models
from .models import Task, TaskExecution, TaskStatus
import logging

logger = logging.getLogger(__name__)


class DAGManager:
    """Gerencia dependências entre tarefas usando DAGs"""
    
    def __init__(self):
        self._dag_cache = {}
    
    def build_dag(self, pipeline_id: int) -> nx.DiGraph:
        """Constrói DAG para um pipeline"""
        if pipeline_id in self._dag_cache:
            return self._dag_cache[pipeline_id]
        
        tasks = Task.objects.filter(pipeline_id=pipeline_id, is_active=True)
        G = nx.DiGraph()
        
        # Adiciona nós (tarefas)
        for task in tasks:
            G.add_node(task.id, task=task)
        
        # Adiciona arestas (dependências)
        for task in tasks:
            for dep in task.depends_on.filter(is_active=True):
                G.add_edge(dep.id, task.id)
        
        # Valida se é DAG (sem ciclos)
        if not nx.is_directed_acyclic_graph(G):
            logger.error(f"Pipeline {pipeline_id} contém ciclos!")
            raise ValueError(f"Pipeline {pipeline_id} contém ciclos nas dependências")
        
        self._dag_cache[pipeline_id] = G
        return G
    
    def can_execute(self, task: Task) -> bool:
        """
        Verifica se uma tarefa pode ser executada
        (todas as dependências foram concluídas com sucesso)
        """
        dependencies = task.depends_on.filter(is_active=True)
        
        if not dependencies.exists():
            return True
        
        # Verifica se todas as dependências tiveram sucesso recentemente
        for dep in dependencies:
            # Busca última execução bem-sucedida da dependência
            last_success = TaskExecution.objects.filter(
                task=dep,
                status=TaskStatus.SUCCESS
            ).order_by('-created_at').first()
            
            if not last_success:
                return False
            
            # Verifica se há execução mais recente que falhou (dependência precisa ser reexecutada)
            last_execution = TaskExecution.objects.filter(
                task=dep
            ).order_by('-created_at').first()
            
            if last_execution and last_execution.status != TaskStatus.SUCCESS:
                return False
        
        return True
    
    def get_ready_tasks(self, pipeline_id: int, completed: Set[int] = None) -> List[Task]:
        """
        Retorna tarefas prontas para execução (dependências satisfeitas)
        """
        if completed is None:
            completed = set()
        
        G = self.build_dag(pipeline_id)
        ready = []
        
        for node_id in G.nodes():
            # Verifica se já foi completada
            if node_id in completed:
                continue
            
            # Verifica se todas as dependências foram completadas
            predecessors = list(G.predecessors(node_id))
            if all(pred_id in completed for pred_id in predecessors):
                task = G.nodes[node_id]['task']
                ready.append(task)
        
        return ready
    
    def get_execution_order(self, pipeline_id: int) -> List[List[Task]]:
        """
        Retorna ordem de execução em camadas (topological sort)
        Cada camada pode ser executada em paralelo
        """
        G = self.build_dag(pipeline_id)
        
        # Gera camadas usando topological generations
        layers = []
        for layer_nodes in nx.topological_generations(G):
            layer_tasks = [G.nodes[node_id]['task'] for node_id in layer_nodes]
            layers.append(layer_tasks)
        
        return layers
    
    def invalidate_cache(self, pipeline_id: int = None):
        """Invalida cache de DAG"""
        if pipeline_id:
            self._dag_cache.pop(pipeline_id, None)
        else:
            self._dag_cache.clear()

