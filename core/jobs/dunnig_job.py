from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_dunning():
    """Напоминания и отмены"""
    logger.info("Dunning job started")
    logger.info("Dunning job completed")