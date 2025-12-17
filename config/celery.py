import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('subscription_system')

# Load configuration from Django settings, all celery configuration should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# ============================================================================
# CELERY BEAT SCHEDULE - Регулярные задачи
# ============================================================================

app.conf.beat_schedule = {
    # Биллинг каждый час
    'process-billing-every-hour': {
        'task': 'apps.subscriptions.tasks.process_billing_cycle',
        'schedule': crontab(minute=0),  # каждый час в начале часа
    },

    # Повторные попытки платежей каждый час в :15
    'retry-failed-payments-every-hour': {
        'task': 'apps.subscriptions.tasks.retry_failed_payments',
        'schedule': crontab(minute=15),  # в :15 каждого часа
    },

    # Напоминание об истечении подписки (каждый день в 09:00)
    'send-expiring-subscription-reminders': {
        'task': 'apps.subscriptions.tasks.send_expiring_subscription_reminders',
        'schedule': crontab(hour=9, minute=0),  # каждый день в 09:00
    },

    # Очистка старых платежей (каждый понедельник в 02:00)
    'cleanup-old-payments': {
        'task': 'apps.payments.tasks.cleanup_old_payments',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),
    },
}

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard time limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft time limit

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task для проверки что Celery работает"""
    print(f'Request: {self.request!r}')