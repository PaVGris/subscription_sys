import pytest
from django.contrib.auth.models import User
from apps.subscriptions.models import Plan
from apps.payments.models import PaymentMethodRef
import factory

@pytest.fixture
def user():
    return User.objects.create_user(email='test@example.com', password='testpass')

@pytest.fixture
def plan():
    return Plan.objects.create(
        name='Basic',
        price_amount=100,
        billing_period='MONTH',
        trial_days=0
    )

@pytest.fixture
def payment_method(user):
    return PaymentMethodRef.objects.create(
        user=user,
        provider='fake',
        provider_customer_id='cust_123',
        provider_payment_method_id='method_123',
        is_default=True
    )