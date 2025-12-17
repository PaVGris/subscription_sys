from datetime import datetime, timedelta
from django.db import transaction
from apps.subscriptions.models import Subscription
from apps.payments.models import Invoice

from apps.payments.models import Payment, TransactionHistoryEntry
from core.payment_gateway import get_payment_gateway
from .subscription_service import SubscriptionService


class BillingService:
    """Сервис для регулярного биллинга подписок"""

    def __init__(self):
        self.gateway = get_payment_gateway()
        self.subscription_service = SubscriptionService()

    def process_billing_cycle(self):
        """Обработать все подписки, готовые к биллингу"""

        now = datetime.now()

        subscriptions = Subscription.objects.filter(
            status='ACTIVE',
            current_period_end__lte=now.date()
        ).select_for_update()

        processed = 0
        failed = 0

        for subscription in subscriptions:
            try:
                self._bill_single_subscription(subscription)
                processed += 1
            except Exception as e:
                print(f"Error billing subscription {subscription.id}: {e}")
                failed += 1

        return {
            'processed': processed,
            'failed': failed,
            'total': processed + failed,
        }

    def _bill_single_subscription(self, subscription):
        """Обработать биллинг одной подписки"""

        with transaction.atomic():
            subscription.refresh_from_db()
            if subscription.status != 'ACTIVE':
                return

            invoice = Invoice.objects.create(
                subscription=subscription,
                user=subscription.user,
                amount=subscription.plan.price_amount,
                currency=subscription.plan.currency,
                status='PENDING',
            )

            payment = self._create_payment_for_invoice(subscription, invoice)

            response = self.gateway.create_payment(payment, None)

            payment.provider_payment_id = response.get('provider_payment_id')
            payment.status = response.get('status', 'FAILED')
            payment.save()

            if response.get('status') == 'SUCCEEDED':
                self._handle_successful_payment(subscription, invoice, payment)
            else:
                self._handle_failed_payment(subscription, invoice, payment)

    @staticmethod
    def _create_payment_for_invoice(subscription, invoice):
        """Создать объект платежа"""

        import hashlib
        idempotency_key = hashlib.sha256(
            f"{subscription.id}:{invoice.id}:{datetime.now():%Y-%m-%d}".encode()
        ).hexdigest()

        payment = Payment.objects.create(
            invoice=invoice,
            user=subscription.user,
            status='PENDING',
            amount=invoice.amount,
            currency=invoice.currency,
            idempotency_key=idempotency_key,
        )

        return payment

    @staticmethod
    def _handle_successful_payment(subscription, invoice, payment):
        """Обработать успешный платёж"""

        invoice.status = 'PAID'
        invoice.save()

        subscription.current_period_start = subscription.current_period_end

        if subscription.plan.billing_period == 'MONTH':
            subscription.current_period_end = (
                    subscription.current_period_end + timedelta(days=30)
            )
        else:
            subscription.current_period_end = (
                    subscription.current_period_end + timedelta(days=365)
            )

        subscription.status = 'ACTIVE'
        subscription.save()

        TransactionHistoryEntry.objects.create(
            user=subscription.user,
            subscription=subscription,
            type='CHARGE',
            amount=payment.amount,
            currency=payment.currency,
        )

        print(f"✅ Subscription {subscription.id} charged successfully")

    @staticmethod
    def _handle_failed_payment(subscription, invoice, payment):
        """Обработать неудачный платёж"""

        invoice.status = 'FAILED'
        invoice.save()

        subscription.status = 'PAST_DUE'
        subscription.save()

        print(f"❌ Payment failed for subscription {subscription.id}")

    def retry_failed_payments(self):
        """Повторить неудачные платежи"""

        failed_payments = Payment.objects.filter(status='FAILED')
        retried = 0

        for payment in failed_payments:
            try:
                # Повтор платежа
                response = self.gateway.create_payment(payment, None)

                payment.provider_payment_id = response.get('provider_payment_id')
                payment.status = response.get('status', 'FAILED')
                payment.retry_count += 1
                payment.save()

                if response.get('status') == 'SUCCEEDED':
                    # Успех - обнови инвойс
                    invoice = payment.invoice
                    invoice.status = 'PAID'
                    invoice.save()

                    # Обнови подписку
                    subscription = invoice.subscription
                    self._handle_successful_payment(subscription, invoice, payment)

                    retried += 1

            except Exception as e:
                print(f"Error retrying payment {payment.id}: {e}")

        return {
            'retried': retried,
            'total': failed_payments.count(),
        }