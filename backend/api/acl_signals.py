"""
Django signal: fire the ACL Celery task whenever a Contract is saved with clauses.
Wire up by calling connect_signals() from the api AppConfig.ready().
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


def connect_signals():
    """Call this from AppConfig.ready() to activate the signal."""
    from core.models import Contract
    post_save.connect(_on_contract_saved, sender=Contract, weak=False)
    logger.info("[ACL] post_save signal connected for Contract")


def _on_contract_saved(sender, instance, created, **kwargs):
    """
    Trigger the ACL pipeline in the background after a contract is created.
    Only fires on creation (not every update) and only when clauses exist.
    """
    if not created:
        return
    try:
        from .acl_tasks import process_contract_acl_task
        process_contract_acl_task.apply_async(
            args=[str(instance.id)],
            countdown=5,   # small delay so clause extraction can finish first
        )
        logger.info(f"[ACL] Queued ACL task for contract {instance.id}")
    except Exception as e:
        logger.warning(f"[ACL] Could not queue task (Celery down?): {e}")
