from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    BILLING_PERIOD_CHOICES = [
        ('MONTH', 'Monthly'),
        ('YEAR', 'Yearly'),
    ]

    name = models.CharField(max_length=100)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    billing_period = models.CharField(
        max_length=10,
        choices=BILLING_PERIOD_CHOICES,
        default='MONTH'
    )
    trial_days = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'

    def __str__(self):
        return f"{self.name} ({self.price_amount} {self.currency})"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('TRIALING', 'Trialing'),
        ('ACTIVE', 'Active'),
        ('PAST_DUE', 'Past Due'),
        ('CANCELED', 'Canceled'),
        ('EXPIRED', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    next_billing_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        indexes = [
            models.Index(fields=['next_billing_at', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
