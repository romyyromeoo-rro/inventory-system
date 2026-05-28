from fastapi import APIRouter
from services.monitoring_service import *
from services.metrics import get_metrics


router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"]
)

@router.get("/monitor")
def monitor():
    return {
        "queue": get_queue_stats(),
        "worker": get_worker_status(),
        "metrics": get_metrics()
    }


@router.get("/status")
def monitoring_status():
    return get_worker_status()


@router.get("/metrics")
def monitoring_metrics():
    return get_metrics()

@router.get("/failed_jobs")
def failed_jobs():
    return get_failed_jobs()


