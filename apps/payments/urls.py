from rest_framework.routers import SimpleRouter  # ← ИЗМЕНИ
from apps.payments.views import (
    PaymentViewSet,
    TransactionHistoryViewSet,
    PaymentMethodRefViewSet,
)

router = SimpleRouter()  # ← ИЗМЕНИ
router.register(r'payment-methods', PaymentMethodRefViewSet, basename='payment-method')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'transactions', TransactionHistoryViewSet, basename='transaction')

urlpatterns = router.urls
