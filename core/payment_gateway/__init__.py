from .base import PaymentGateway
from .fake import FakeGateway

def get_payment_gateway():
    """Возвращает экземпляр платёжного шлюза"""
    return FakeGateway()

__all__ = ['PaymentGateway', 'FakeGateway', 'get_payment_gateway']