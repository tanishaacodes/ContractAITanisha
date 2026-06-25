"""
Celery Async Tasks for Bid Management
======================================
Tasks:
  generate_bid_actions_task       — async action item generation
  run_risk_propagation_task       — async DFS risk cascade
  snapshot_readiness_task         — async readiness snapshot
  train_delay_model_task          — bootstrap/retrain ML delay model
  full_bid_orchestration_task     — run all steps in sequence
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30,
             time_limit=300, soft_time_limit=270,
             name='tenders.generate_bid_actions')
def generate_bid_actions_task(self, tender_id: int, regenerate: bool = False):
    """
    Async: generate BidActionItem rows for a tender.
    Called after tender analysis completes.
    """
    try:
        from tenders.models import Tender
        from tenders.services.action_generator import (
            generate_action_items, seed_departments,
        )

        tender = Tender.objects.get(id=tender_id)
        seed_departments()
        count = generate_action_items(tender, regenerate=regenerate)
        logger.info(f"[Task] Generated {count} action items for tender {tender_id}")
        return {'status': 'success', 'count': count}

    except Tender.DoesNotExist:
        logger.error(f"[Task] Tender {tender_id} not found")
        return {'status': 'error', 'message': 'Tender not found'}

    except Exception as exc:
        logger.exception(f"[Task] generate_bid_actions_task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30,
             time_limit=120, soft_time_limit=100,
             name='tenders.run_risk_propagation')
def run_risk_propagation_task(self, tender_id: int):
    """
    Async: run DFS risk cascade + persist BidDepartmentRiskPropagation rows.
    """
    try:
        from tenders.models import Tender
        from tenders.services.propagation_engine import propagate_and_store

        tender  = Tender.objects.get(id=tender_id)
        results = propagate_and_store(tender)
        logger.info(f"[Task] Risk propagation complete for tender {tender_id}: "
                    f"{len(results)} departments")
        return {'status': 'success', 'departments': len(results)}

    except Tender.DoesNotExist:
        logger.error(f"[Task] Tender {tender_id} not found")
        return {'status': 'error', 'message': 'Tender not found'}

    except Exception as exc:
        logger.exception(f"[Task] run_risk_propagation_task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=15,
             time_limit=60, soft_time_limit=50,
             name='tenders.snapshot_readiness')
def snapshot_readiness_task(self, tender_id: int):
    """
    Async: save a BidReadinessSnapshot row for the tender.
    """
    try:
        from tenders.models import Tender
        from tenders.services.readiness_engine import snapshot_readiness

        tender = Tender.objects.get(id=tender_id)
        snap   = snapshot_readiness(tender)
        logger.info(f"[Task] Readiness snapshot saved for tender {tender_id}: "
                    f"{snap.readiness_index}%")
        return {'status': 'success', 'readiness_index': snap.readiness_index}

    except Tender.DoesNotExist:
        logger.error(f"[Task] Tender {tender_id} not found")
        return {'status': 'error', 'message': 'Tender not found'}

    except Exception as exc:
        logger.exception(f"[Task] snapshot_readiness_task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1,
             time_limit=600, soft_time_limit=550,
             name='tenders.train_delay_model')
def train_delay_model_task(self):
    """
    Async: train / retrain the GradientBoosting delay prediction model.
    Uses synthetic data if no historical data is available.
    """
    try:
        from tenders.services.delay_model import ensure_model_trained
        ensure_model_trained()
        logger.info("[Task] Delay model training complete")
        return {'status': 'success'}

    except Exception as exc:
        logger.exception(f"[Task] train_delay_model_task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60,
             time_limit=600, soft_time_limit=550,
             name='tenders.full_bid_orchestration')
def full_bid_orchestration_task(self, tender_id: int):
    """
    Async: Run the full bid management pipeline in sequence:
      1. Generate action items
      2. Run risk propagation
      3. Save readiness snapshot
    Called automatically after a tender is fully analyzed.
    """
    try:
        from tenders.models import Tender
        from tenders.services.action_generator import (
            generate_action_items, seed_departments,
        )
        from tenders.services.propagation_engine import propagate_and_store
        from tenders.services.readiness_engine import snapshot_readiness

        tender = Tender.objects.get(id=tender_id)

        # Step 1 — Action items
        seed_departments()
        count = generate_action_items(tender, regenerate=False)
        logger.info(f"[Orchestration] Step 1 done: {count} action items")

        # Step 2 — Risk propagation
        results = propagate_and_store(tender)
        logger.info(f"[Orchestration] Step 2 done: {len(results)} depts")

        # Step 3 — Readiness snapshot
        snap = snapshot_readiness(tender)
        logger.info(f"[Orchestration] Step 3 done: {snap.readiness_index}% ready")

        return {
            'status':          'success',
            'action_count':    count,
            'dept_count':      len(results),
            'readiness_index': snap.readiness_index,
        }

    except Tender.DoesNotExist:
        logger.error(f"[Orchestration] Tender {tender_id} not found")
        return {'status': 'error', 'message': 'Tender not found'}

    except Exception as exc:
        logger.exception(f"[Orchestration] full_bid_orchestration_task failed: {exc}")
        raise self.retry(exc=exc)
