import hashlib
from datetime import datetime, timedelta
from django.db import transaction
from apps.subscriptions.models import Subscription, Plan
from apps.payments.models import Invoice
from apps.payments.models import Payment, PaymentMethodRef, TransactionHistoryEntry
from core.payment_gateway import get_payment_gateway
from celery import current_app as celery_app

class SubscriptionService:
    def __init__(self):
        self.gateway = get_payment_gateway()

    def create_subscription(self, user, plan_id, payment_method_id=None):
        """Создать новую подписку (обновленная версия)"""

        plan = Plan.objects.get(id=plan_id)
        payment_method = None
        if payment_method_id:
            payment_method = PaymentMethodRef.objects.get(id=payment_method_id)

        with transaction.atomic():
            now = datetime.now()
            status = 'TRIALING' if plan.trial_days > 0 else 'ACTIVE'

            current_period_start = now.date()
            if plan.billing_period == 'MONTH':
                current_period_end = (now + timedelta(days=30)).date()
            else:
                current_period_end = (now + timedelta(days=365)).date()

            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                status=status,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
            )

            invoice_amount = 0 if plan.trial_days > 0 else plan.price_amount

            invoice = Invoice.objects.create(
                subscription=subscription,
                user=user,
                amount=invoice_amount,
                status='PENDING' if invoice_amount > 0 else 'PAID',
            )

            if invoice_amount > 0 and payment_method:
                self._process_payment(subscription, invoice, payment_method)

            return subscription

    def _process_payment(self, subscription, invoice, payment_method):
        """Обработать платёж"""

        idempotency_key = self._generate_idempotency_key(
            subscription.id,
            invoice.id
        )

        existing = Payment.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return existing

        payment = Payment.objects.create(
            invoice=invoice,
            user=subscription.user,
            status='PENDING',
            amount=invoice.amount,
            provider_payment_id=None,
            idempotency_key=idempotency_key,
        )

        try:
            response = self.gateway.create_payment(payment, payment_method)

            payment.provider_payment_id = response.get('provider_payment_id')
            payment.status = response.get('status', 'FAILED')
            payment.save()

            if response.get('status') == 'SUCCEEDED':
                invoice.status = 'PAID'
                invoice.save()

                subscription.status = 'ACTIVE'
                subscription.save()

                TransactionHistoryEntry.objects.create(
                    user=subscription.user,
                    subscription=subscription,
                    type='CHARGE',
                    amount=payment.amount,
                )
            else:
                invoice.status = 'FAILED'
                invoice.save()
                subscription.status = 'PAST_DUE'
                subscription.save()

        except Exception as e:
            payment.status = 'ERROR'
            payment.save()
            raise

        return payment

    @staticmethod
    def cancel_subscription(subscription_id, immediate=False):
        """Отменить подписку"""

        subscription = Subscription.objects.get(id=subscription_id)

        if immediate:
            subscription.status = 'CANCELED'
        else:
            subscription.cancel_at_period_end = True

        subscription.save()
        return subscription

    @staticmethod
    def _generate_idempotency_key(subscription_id, invoice_id):
        """Генерирует уникальный ключ для идемпотентности"""
        key = f"{subscription_id}:{invoice_id}:{datetime.now():%Y-%m-%d}"
        return hashlib.sha256(key.encode()).hexdigest()