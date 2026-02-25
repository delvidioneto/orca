"""Utilitários do scheduler."""
from .models import ScheduleType


def infer_schedule_type(config):
    """
    Infere o schedule_type a partir do JSON de configuração.
    Assim o formulário pode ter só o campo JSON e o tipo é definido automaticamente.
    Lista de {hour, minute} = diário com vários horários (DAILY).
    """
    if not config:
        return ScheduleType.DAILY
    if isinstance(config, list):
        return ScheduleType.DAILY
    if not isinstance(config, dict):
        return ScheduleType.DAILY
    # Intervalo: seconds, minutes, hours ou days
    if any(k in config for k in ('seconds', 'minutes', 'hours', 'days')):
        return ScheduleType.INTERVAL
    # Quinzenal: week presente (ex: "*/2")
    if 'week' in config:
        return ScheduleType.BIWEEKLY
    # Mensal: dia do mês (1-31)
    if 'day' in config:
        return ScheduleType.MONTHLY
    # Semanal: dia da semana (0-6)
    if 'day_of_week' in config:
        return ScheduleType.WEEKLY
    # Cron completo (year, month, day, etc.) -> CRON
    if any(k in config for k in ('year', 'month', 'second')):
        return ScheduleType.CRON
    # Padrão: diário (hour, minute opcionais)
    return ScheduleType.DAILY
