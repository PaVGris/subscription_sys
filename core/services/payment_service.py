from apps.payments.models import Payment, TransactionHistoryEntry
from core.payment_gateway import get_payment_gateway


class PaymentService:
    """Сервис для управления платежами"""

    def __init__(self):
        self.gateway = get_payment_gateway()

    def refund_payment(self, payment_id, amount=None):
        """Вернуть деньги за платёж"""

        payment = Payment.objects.get(id=payment_id)

        if amount is None:
            amount = payment.amount

        response = self.gateway.refund_payment(
            payment,
            amount,
            reason='User requested refund'
        )

        TransactionHistoryEntry.objects.create(
            user=payment.user,
            subscription=payment.invoice.subscription,
            type='REFUND',
            amount=amount,
            currency=payment.currency,
        )

        return response

    @staticmethod
    def list_user_payments(user):
        """Получить все платежи пользователя"""
        return Payment.objects.filter(user=user).order_by('-created_at')

    @staticmethod
    def list_user_transactions(user):
        """Получить всю историю операций пользователя"""
        return TransactionHistoryEntry.objects.filter(
            user=user
        ).order_by('-created_at')