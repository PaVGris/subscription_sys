from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def retry_failed_payments():
    """Повторные попытки"""
    logger.info("Retry job started")
    logger.info("Retry job completed")