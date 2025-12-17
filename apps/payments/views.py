from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import logging

from apps.payments.models import Payment, TransactionHistoryEntry, PaymentMethodRef
from apps.payments.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    TransactionHistorySerializer,
    PaymentMethodRefSerializer,
)
from core.services import PaymentService

logger = logging.getLogger(__name__)


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentMethodRefViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodRefSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        return PaymentMethodRef.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def refund(self, request, pk=None):
        try:
            payment = self.get_object()
            amount = request.data.get('amount', payment.amount)

            service = PaymentService()
            response = service.refund_payment(payment.id, amount=amount)

            return Response(
                {'status': 'Refund initiated', 'payment_id': payment.id},
                status=status.HTTP_200_OK
            )

        except Payment.DoesNotExist:
            logger.error(f"Payment {pk} not found")
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error refunding payment: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransactionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return TransactionHistoryEntry.objects.filter(user=self.request.user)