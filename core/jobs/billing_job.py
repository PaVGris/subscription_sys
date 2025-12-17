from celery import shared_task
from core.services import BillingService

@shared_task
def process_billing():
    """Запускается каждый час"""
    service = BillingService()
    result = service.process_billing_cycle()
    print(f"Billing: {result}")
    return result

@shared_task
def retry_failed_payments():
    """Запускается каждый час в :15"""
    service = BillingService()
    result = service.retry_failed_payments()
    print(f"Retry: {result}")
    return result