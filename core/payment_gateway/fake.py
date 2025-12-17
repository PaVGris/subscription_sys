import hashlib
import random
from datetime import datetime
from .base import PaymentGateway


class FakeGateway(PaymentGateway):
    """Фейковый шлюз для разработки"""

    def __init__(self, failure_rate=0.1):
        self.failure_rate = failure_rate

    def create_payment(self, payment, method):
        should_fail = random.random() < self.failure_rate
        return {
            'provider_payment_id': hashlib.sha256(
                f"{payment.id}{datetime.now()}".encode()
            ).hexdigest(),
            'status': 'FAILED' if should_fail else 'SUCCEEDED',
            'error_code': None if not should_fail else 'ERROR',
            'created_at': datetime.now(),
        }

    def refund_payment(self, payment, amount, reason):
        return {'status': 'SUCCEEDED'}

    def get_payment_status(self, provider_payment_id):
        return {'status': 'SUCCEEDED'}

    def save_payment_method(self, user_id, payment_token):
        return {'provider_payment_id': hashlib.sha256(
            f"{user_id}_{payment_token}".encode()
        ).hexdigest()}