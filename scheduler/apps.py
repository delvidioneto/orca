from django.apps import AppConfig
import os


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'
    
    def ready(self):
        """Inicia o scheduler quando o app está pronto (apenas em produção/runserver)"""
        # Só inicia se não estiver em modo de teste ou migração
        if os.environ.get('RUN_MAIN') == 'true' and not os.environ.get('TESTING'):
            try:
                from .scheduler_manager import SchedulerManager
                scheduler_manager = SchedulerManager()
                if not scheduler_manager.is_running:
                    scheduler_manager.start()
            except Exception as e:
                # Log mas não quebra a aplicação
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro ao iniciar scheduler: {e}")

