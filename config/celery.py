import os
from celery import Celery
from celery.schedules import crontab

# Установить модуль настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('subscription_system')

# Загрузить конфигурацию из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks из всех зарегистрированных Django apps
app.autodiscover_tasks()

# Расписание для Celery Beat
app.conf.beat_schedule = {
    'process-billing-every-hour': {
        'task': 'apps.subscriptions.tasks.process_billing_cycle',
        'schedule': crontab(minute=0),  # Каждый час в :00
    },
    'retry-failed-payments-every-hour': {
        'task': 'apps.subscriptions.tasks.retry_failed_payments',
        'schedule': crontab(minute=15),  # Каждый час в :15
    },
    'cleanup-old-payments': {
        'task': 'apps.payments.tasks.cleanup_old_payments',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Понедельник в 02:00
    },
}

# Настройки задач
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут hard time limit
    task_soft_time_limit=25 * 60,  # 25 минут soft time limit
    result_expires=3600,  # Результаты истекают через 1 час
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task для Celery"""
    print(f'Request: {self.request!r}')