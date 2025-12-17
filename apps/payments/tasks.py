import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from apps.payments.models import Payment, TransactionHistoryEntry

logger = logging.getLogger(__name__)


# ============================================================================
# ЗАДАЧИ ДЛЯ ОЧИСТКИ И АРХИВИРОВАНИЯ
# ============================================================================

@shared_task(bind=True, max_retries=2)
def cleanup_old_payments(self):
    """
    Архивировать и удалять очень старые платежи (старше 90 дней)

    Запускается каждый понедельник в 02:00
    """
    try:
        logger.info("🧹 Starting cleanup of old payments...")

        # Ищем платежи старше 90 дней
        ninety_days_ago = timezone.now() - timedelta(days=90)

        old_payments = Payment.objects.filter(
            created_at__lt=ninety_days_ago
        )

        count = old_payments.count()

        # В production можно архивировать в отдельную таблицу
        # Сейчас просто логируем
        logger.info(f"Found {count} old payments to cleanup")

        # Удаляем raw_request и raw_response для экономии места
        old_payments.update(
            raw_request=None,
            raw_response=None
        )

        logger.info(f"✅ Cleaned up {count} old payments")
        return {'cleaned': count}

    except Exception as exc:
        logger.error(f"❌ Error in cleanup: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=3600)


@shared_task
def generate_payment_report(period_start, period_end):
    """
    Генерировать отчёт по платежам за период

    Используется для бухгалтерии
    """
    try:
        logger.info(f"📊 Generating payment report for {period_start} - {period_end}...")

        payments = Payment.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end,
            status='SUCCEEDED'
        )

        total_amount = sum(p.amount for p in payments)
        total_count = payments.count()

        report = {
            'period_start': str(period_start),
            'period_end': str(period_end),
            'total_payments': total_count,
            'total_amount': float(total_amount),
            'average_amount': float(total_amount / total_count) if total_count > 0 else 0,
        }

        logger.info(f"✅ Payment report generated: {report}")
        return report

    except Exception as exc:
        logger.error(f"❌ Error generating report: {exc}", exc_info=True)


# ============================================================================
# ЗАДАЧИ ДЛЯ МОНИТОРИНГА
# ============================================================================

@shared_task
def monitor_failed_payments():
    """
    Мониторить количество неудачных платежей

    Если много ошибок - отправить алерт
    """
    try:
        # Ищем платежи с ошибками за последний час
        one_hour_ago = timezone.now() - timedelta(hours=1)

        failed_payments = Payment.objects.filter(
            status__in=['FAILED', 'ERROR'],
            created_at__gte=one_hour_ago
        )

        failed_count = failed_payments.count()

        if failed_count > 10:
            logger.warning(
                f"⚠️ ALERT: {failed_count} failed payments in the last hour!"
            )
            # Здесь можно отправить alert в Slack или другой сервис

        logger.info(f"✅ Failed payments monitoring: {failed_count} issues found")
        return {'failed_count': failed_count}

    except Exception as exc:
        logger.error(f"❌ Error in monitoring: {exc}", exc_info=True)