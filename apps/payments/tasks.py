import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from apps.payments.models import Payment

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def cleanup_old_payments(self):
    """Очистить старые платежи (старше 90 дней)"""
    try:
        logger.info("🧹 Starting cleanup of old payments...")

        ninety_days_ago = timezone.now() - timedelta(days=90)
        old_payments = Payment.objects.filter(created_at__lt=ninety_days_ago)
        count = old_payments.count()

        logger.info(f"Found {count} old payments to cleanup")

        # Очистить raw request/response для экономии места
        old_payments.update(raw_request=None, raw_response=None)

        logger.info(f"✅ Cleaned up {count} old payments")
        return {'cleaned': count}

    except Exception as exc:
        logger.error(f"❌ Error in cleanup: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=3600)