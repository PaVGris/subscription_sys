from rest_framework.routers import SimpleRouter  # ← ИЗМЕНИ
from apps.subscriptions.views import PlanViewSet, SubscriptionViewSet

router = SimpleRouter()  # ← ИЗМЕНИ
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = router.urls
