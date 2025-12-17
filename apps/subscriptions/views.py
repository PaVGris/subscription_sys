from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    SubscriptionDetailSerializer,
    SubscriptionUpdateSerializer,
)
from core.services import SubscriptionService


class StandardPageNumberPagination(PageNumberPagination):
    """Стандартная пагинация"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для планов подписки

    GET /api/plans/              - Список всех активных планов
    GET /api/plans/{id}/         - Детали плана
    """
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    pagination_class = StandardPageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['price_amount', 'created_at']
    ordering = ['price_amount']


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для подписок пользователя

    GET    /api/subscriptions/           - Список подписок пользователя
    POST   /api/subscriptions/           - Создать новую подписку
    GET    /api/subscriptions/{id}/      - Детали подписки
    PATCH  /api/subscriptions/{id}/      - Обновить подписку
    DELETE /api/subscriptions/{id}/      - Удалить подписку
    POST   /api/subscriptions/{id}/cancel/ - Отменить подписку
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'plan']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает подписки только текущего пользователя"""
        return Subscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия"""
        if self.action == 'retrieve':
            return SubscriptionDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        """
        Создать новую подписку

        POST /api/subscriptions/
        {
            "plan_id": 1,
            "payment_method_id": 1  (опционально)
        }
        """
        try:
            service = SubscriptionService()
            subscription = service.create_subscription(
                user=request.user,
                plan_id=request.data.get('plan_id'),
                payment_method_id=request.data.get('payment_method_id'),
            )
            serializer = SubscriptionDetailSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Plan.DoesNotExist:
            return Response(
                {'error': 'План не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление подписки

        PATCH /api/subscriptions/{id}/
        {
            "cancel_at_period_end": true
        }
        """
        subscription = self.get_object()

        if 'cancel_at_period_end' in request.data:
            subscription.cancel_at_period_end = request.data.get('cancel_at_period_end')
            subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удалить подписку (отменить немедленно)

        DELETE /api/subscriptions/{id}/
        """
        subscription = self.get_object()
        service = SubscriptionService()
        service.cancel_subscription(subscription.id, immediate=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Отменить подписку

        POST /api/subscriptions/{id}/cancel/
        {
            "immediate": false  (true - сейчас, false - в конце периода)
        }
        """
        try:
            service = SubscriptionService()
            immediate = request.data.get('immediate', False)
            subscription = service.cancel_subscription(pk, immediate=immediate)

            serializer = SubscriptionDetailSerializer(subscription)
            return Response(serializer.data)

        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )