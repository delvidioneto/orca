import subprocess
import logging
import yaml
import time
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# === Setup de log ===
logging.basicConfig(
    filename='logs/orca.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def run_task(name, script):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Executando: {name} às {hora}")
    logging.info(f"[{name}] [{hora}] Iniciando script: {script}")
    try:
        subprocess.run(['python', script], check=True)
        logging.info(f"[{name}] [{hora}] Finalizado com sucesso")
    except subprocess.CalledProcessError as e:
        logging.error(f"[{name}] [{hora}] ERRO na execução: {e}")
        print(f"❌ ERRO na tarefa {name}: {e}")

def load_pipeline(path='pipeline.yml'):
    with open(path) as f:
        return yaml.safe_load(f)['tasks']

def schedule_all(tasks):
    sched = BackgroundScheduler(timezone=timezone('America/Sao_Paulo'))
    for task in tasks:
        trigger_config = task['trigger'].copy()
        tipo = trigger_config.pop('type', 'cron')

        if tipo == 'cron':
            trig = CronTrigger(**trigger_config)
        elif tipo == 'interval':
            trig = IntervalTrigger(**trigger_config)
        else:
            logging.error(f"[{task['name']}] Tipo de trigger inválido: {tipo}")
            continue

        sched.add_job(
            run_task,
            trigger=trig,
            args=[task['name'], task['script']],
            id=task['name'],
            name=task['name']
        )

        logging.info(f"[{task['name']}] Agendada com trigger: {trigger_config}")
        print(f"📅 Tarefa '{task['name']}' agendada com trigger: {trigger_config}")
    return sched

if __name__ == '__main__':
    print("🐋 ORCA INICIADO")
    logging.info("=== Iniciando Orca ===")
    tasks = load_pipeline()
    scheduler = schedule_all(tasks)
    print("✅ Aguardando execuções...")
    try:
        scheduler.start()
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("=== ORCA encerrado ===")
        print("🛑 Orca finalizado")
