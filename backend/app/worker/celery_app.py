from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "sara_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat Periodic Schedule
celery_app.conf.beat_schedule = {
    "evaluate-slas-every-minute": {
        "task": "app.worker.tasks.evaluate_grievance_slas_task",
        "schedule": 60.0, # Evaluate active grievances every 60 seconds
    },
    "update-analytics-snapshots-hourly": {
        "task": "app.worker.tasks.update_analytics_snapshots_task",
        "schedule": 3600.0, # Run hourly
    }
}

# Import tasks module to register task signatures
import app.worker.tasks

# Simple placeholder task to verify worker initialization
@celery_app.task(name="app.worker.celery_app.ping")
def ping():
    return "pong"
