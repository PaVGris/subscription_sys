import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from apps.subscriptions.models import Subscription, Plan
from apps.payments.models import TransactionHistoryEntry
from core.services import BillingService, SubscriptionService
from core.services import NotificationService

logger = logging.getLogger(__name__)


# ============================================================================
# БИЛЛИНГ ЗАДАЧИ
# ============================================================================

@shared_task(bind=True, max_retries=3)
def process_billing_cycle(self):
    """Обработать все подписки, готовые к биллингу"""
    try:
        logger.info("🔄 Starting billing cycle...")

        service = BillingService()
        result = service.process_billing_cycle()

        # ✅ Отправить уведомления после успешных платежей
        for subscription_id in result.get('processed_subscriptions', []):
            subscription = Subscription.objects.get(id=subscription_id)
            try:
                payment = Payment.objects.filter(
                    invoice__subscription=subscription
                ).latest('created_at')

                if payment.status == 'SUCCEEDED':
                    NotificationService.send_payment_success(
                        payment,
                        payment.invoice
                    )
            except Payment.DoesNotExist:
                pass

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
    """
    Повторить неудачные платежи

    Запускается каждый час в :15
    """
    try:
        logger.info("🔄 Starting retry failed payments...")

        service = BillingService()
        result = service.retry_failed_payments()

        logger.info(f"✅ Retried failed payments: retried={result['retried']}")

        return result

    except Exception as exc:
        logger.error(f"❌ Error in retry payments: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)

@shared_task(bind=True, max_retries=3)
def send_payment_failed_email(self, payment_id):
    """
    Отправить email об ошибке платежа

    Вызывается после неудачного платежа
    """
    try:
        logger.info(f"📧 Sending payment failed email for payment {payment_id}...")

        from apps.payments.models import Payment

        payment = Payment.objects.get(id=payment_id)
        subscription = payment.invoice.subscription

        subject = "❌ Ошибка при обработке платежа"
        message = f"""
        Привет {payment.user.first_name or payment.user.username}!

        К сожалению, не удалось обработать ваш платёж.
        Сумма: {payment.amount} {payment.currency}
        Подписка: {subscription.plan.name}

        Пожалуйста, попробуйте позже или обновите способ оплаты.
        Если проблема повторится, свяжитесь с нашей поддержкой.

        Спасибо!
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [payment.user.email],
            fail_silently=False,
        )

        logger.info(f"✅ Payment failed email sent to {payment.user.email}")

    except Exception as exc:
        logger.error(f"❌ Error sending payment failed email: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=600)
