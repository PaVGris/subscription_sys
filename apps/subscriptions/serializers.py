from rest_framework import serializers
from apps.subscriptions.models import Plan, Subscription
from apps.payments.models import Invoice

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price_amount', 'currency', 'billing_period', 'trial_days', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'subscription', 'amount', 'currency', 'status', 'billing_period_start', 'billing_period_end', 'created_at']
        read_only_fields = ['id', 'created_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'plan_id', 'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    invoices = InvoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end', 'invoices', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'invoices', 'created_at', 'updated_at']


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['status', 'cancel_at_period_end']
