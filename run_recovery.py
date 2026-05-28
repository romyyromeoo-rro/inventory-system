import time
from core.logger import logger
from services.recovery_service import (
    recover_stuck_jobs
)

logger.info("Recovery Service Started")

while True:
    recovered = recover_stuck_jobs()

    if recovered > 0:
        logger.warning(f"Recovered {recovered} jobs")
        time.sleep(5)
