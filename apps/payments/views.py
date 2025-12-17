from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.payments.models import Payment, TransactionHistoryEntry, PaymentMethodRef
from apps.payments.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    TransactionHistorySerializer,
    PaymentMethodRefSerializer,
)
from core.services import PaymentService


class StandardPageNumberPagination(PageNumberPagination):
    """Стандартная пагинация"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentMethodRefViewSet(viewsets.ModelViewSet):
    """
    ViewSet для способов оплаты

    GET    /api/payment-methods/         - Список способов оплаты
    POST   /api/payment-methods/         - Добавить способ оплаты
    GET    /api/payment-methods/{id}/    - Детали способа оплаты
    PATCH  /api/payment-methods/{id}/    - Обновить способ оплаты
    DELETE /api/payment-methods/{id}/    - Удалить способ оплаты
    """
    serializer_class = PaymentMethodRefSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['provider', 'is_default']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает способы оплаты только текущего пользователя"""
        return PaymentMethodRef.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Добавить пользователя при создании"""
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для платежей

    GET    /api/payments/            - Список платежей пользователя
    GET    /api/payments/{id}/       - Детали платежа
    POST   /api/payments/{id}/refund/ - Вернуть платёж
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'provider']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает платежи только текущего пользователя"""
        return Payment.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия"""
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Вернуть платёж

        POST /api/payments/{id}/refund/
        {
            "amount": 99.99  (опционально, если не указано - полный возврат)
        }
        """
        try:
            service = PaymentService()
            amount = request.data.get('amount')

            service.refund_payment(pk, amount=amount)

            # Обновляем данные платежа
            payment = self.get_object()
            serializer = PaymentDetailSerializer(payment)

            return Response(serializer.data)

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Платёж не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransactionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для истории операций

    GET    /api/transactions/           - История операций пользователя
    GET    /api/transactions/{id}/      - Детали операции
    """
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type', 'subscription']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает операции только текущего пользователя"""
        return TransactionHistoryEntry.objects.filter(user=self.request.user)