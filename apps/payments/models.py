from django.db import models
from django.contrib.auth.models import User
from apps.subscriptions.models import Subscription, Invoice


class PaymentMethodRef(models.Model):
    PROVIDER_CHOICES = [
        ('fake', 'Fake Gateway'),
        ('yoomoney', 'YooMoney'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    provider_customer_id = models.CharField(max_length=255, null=True, blank=True)
    provider_payment_method_id = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'

    def __str__(self):
        return f"{self.user.email} - {self.provider}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('PENDING', 'Pending'),
        ('SUCCEEDED', 'Succeeded'),
        ('FAILED', 'Failed'),
        ('CANCELED', 'Canceled'),
        ('ERROR', 'Error'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50, default='fake')
    provider_payment_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)
    raw_request = models.TextField(null=True, blank=True)
    raw_response = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['next_retry_at', 'status']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.status}"


class TransactionHistoryEntry(models.Model):
    TYPE_CHOICES = [
        ('CHARGE', 'Charge'),
        ('REFUND', 'Refund'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    related_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_history'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.type} {self.amount} {self.currency}"