import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from apps.subscriptions.models import Subscription
from apps.payments.models import Payment
from core.services import BillingService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_billing_cycle(self):
    """Обработать цикл биллинга"""
    try:
        logger.info("🔄 Starting billing cycle...")

        service = BillingService()
        result = service.process_billing_cycle()

        logger.info(
            f"✅ Billing cycle completed: "
            f"processed={result['processed']}, "
            f"failed={result['failed']}"
        )

        return result

    except Exception as exc:
        logger.error(f"❌ Error in billing cycle: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def retry_failed_payments(self):
    """Повторить неудачные платежи"""
    try:
        logger.info("🔄 Starting retry failed payments...")

        service = BillingService()
        result = service.retry_failed_payments()

        logger.info(
            f"✅ Retried failed payments: "
            f"retried={result['retried']}"
        )

        return result

    except Exception as exc:
        logger.error(f"❌ Error in retry payments: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)