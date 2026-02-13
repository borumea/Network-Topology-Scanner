import logging
from celery import Celery

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "network_topology_mapper",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "full-scan-every-6h": {
            "task": "app.tasks.scan_tasks.scheduled_full_scan",
            "schedule": 21600.0,
        },
        "snmp-poll-every-30m": {
            "task": "app.tasks.scan_tasks.scheduled_snmp_poll",
            "schedule": 1800.0,
        },
        "analysis-every-1h": {
            "task": "app.tasks.analysis_tasks.run_analysis",
            "schedule": 3600.0,
        },
    },
)
