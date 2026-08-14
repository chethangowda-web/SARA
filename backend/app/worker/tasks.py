import asyncio
import logging
from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.governance.services import evaluate_grievance_slas
from app.analytics.services import create_analytics_snapshots

logger = logging.getLogger("sara_worker_tasks")

@celery_app.task(name="app.worker.tasks.evaluate_grievance_slas_task")
def evaluate_grievance_slas_task():
    """
    Periodic task to evaluate SLA warning/breach status for all active grievances.
    """
    async def run_evaluation():
        async with SessionLocal() as db:
            try:
                await evaluate_grievance_slas(db)
            except Exception as e:
                logger.error(f"SLA Evaluation task failed: {e}")
                await db.rollback()
                raise e
                
    try:
        asyncio.run(run_evaluation())
    except Exception as e:
        logger.error(f"SLA Evaluation task wrapper exception: {e}")

@celery_app.task(name="app.worker.tasks.update_analytics_snapshots_task")
def update_analytics_snapshots_task():
    """
    Periodic task to create analytics snapshots and detect anomalies.
    """
    async def run_analytics():
        async with SessionLocal() as db:
            try:
                await create_analytics_snapshots(db)
            except Exception as e:
                logger.error(f"Analytics Snapshot task failed: {e}")
                await db.rollback()
                raise e
                
    try:
        asyncio.run(run_analytics())
    except Exception as e:
        logger.error(f"Analytics Snapshot task wrapper exception: {e}")
