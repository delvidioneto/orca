"""
Comando para iniciar o scheduler manualmente
"""
from django.core.management.base import BaseCommand
from scheduler.scheduler_manager import SchedulerManager


class Command(BaseCommand):
    help = 'Inicia o scheduler do Orca'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando scheduler...'))
        scheduler = SchedulerManager()
        
        if scheduler.is_running:
            self.stdout.write(self.style.WARNING('Scheduler já está rodando'))
        else:
            scheduler.start()
            self.stdout.write(self.style.SUCCESS('Scheduler iniciado com sucesso!'))
            self.stdout.write('Pressione Ctrl+C para parar...')
            
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nParando scheduler...'))
                scheduler.stop()
                self.stdout.write(self.style.SUCCESS('Scheduler parado'))

