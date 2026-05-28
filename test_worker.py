from services.task_queue import push_existing_job
import uuid
import time

push_existing_job({
    "job_id": str(uuid.uuid4()),
    "type": "log_action",
    "payload": {
        "username": "romeo",
        "action": "HEALTH_CHECK"
    },
    "retry": 0,
    "created_at": time.time()

})
