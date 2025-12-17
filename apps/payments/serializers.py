from rest_framework import serializers
from apps.payments.models import Payment, TransactionHistoryEntry, PaymentMethodRef

class PaymentMethodRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethodRef
        fields = [
            'id',
            'user',
            'provider',
            'stripe_payment_method_id',
            'is_default',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'invoice', 'amount', 'currency', 'status',
            'provider', 'provider_payment_id', 'idempotency_key',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'provider_payment_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Автоматически заполни user из request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор платежа"""
    invoice_details = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'invoice',
            'invoice_details',
            'status',
            'amount',
            'currency',
            'provider',
            'provider_payment_id',
            'raw_request',
            'raw_response',
            'retry_count',
            'next_retry_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    @staticmethod
    def get_invoice_details(obj):
        """Получить детали счёта"""
        from apps.subscriptions.serializers import InvoiceSerializer
        return InvoiceSerializer(obj.invoice).data


class TransactionHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории операций"""
    subscription_name = serializers.CharField(
        source='subscription.plan.name',
        read_only=True
    )

    class Meta:
        model = TransactionHistoryEntry
        fields = [
            'id',
            'subscription',
            'subscription_name',
            'type',
            'amount',
            'currency',
            'description',
            'created_at',
        ]
        read_only_fields = fields