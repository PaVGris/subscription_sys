from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    SubscriptionDetailSerializer,
    SubscriptionUpdateSerializer,
)
from core.services import SubscriptionService

logger = logging.getLogger(__name__)


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    pagination_class = StandardPageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['price_amount', 'created_at']
    ordering = ['price_amount']


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'plan']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        try:
            plan_id = request.data.get('plan_id')
            payment_method_id = request.data.get('payment_method_id')

            if not plan_id:
                return Response(
                    {'error': 'plan_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = SubscriptionService()
            subscription = service.create_subscription(
                user=request.user,
                plan_id=plan_id,
                payment_method_id=payment_method_id,
            )

            serializer = SubscriptionDetailSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating subscription: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        subscription = self.get_object()

        if 'cancel_at_period_end' in request.data:
            subscription.cancel_at_period_end = request.data.get('cancel_at_period_end')
            subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        subscription = self.get_object()

        try:
            service = SubscriptionService()
            service.cancel_subscription(subscription.id, immediate=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting subscription: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        try:
            service = SubscriptionService()
            immediate = request.data.get('immediate', False)

            subscription = service.cancel_subscription(pk, immediate=immediate)
            serializer = SubscriptionDetailSerializer(subscription)
            return Response(serializer.data)

        except Subscription.DoesNotExist:
            logger.error(f"Subscription {pk} not found")
            return Response(
                {'error': 'Subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )