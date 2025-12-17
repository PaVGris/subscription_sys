from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Абстрактный класс для платёжных шлюзов"""

    @abstractmethod
    def create_payment(self, payment, method):
        pass

    @abstractmethod
    def refund_payment(self, payment, amount, reason):
        pass

    @abstractmethod
    def get_payment_status(self, provider_payment_id):
        pass

    @abstractmethod
    def save_payment_method(self, user_id, payment_token):
        pass