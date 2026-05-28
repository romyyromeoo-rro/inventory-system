from services.task_queue import push_task
import time

TOTAL_JOB = 1000

start = time.time()

for i in range(TOTAL_JOB):
    push_task({
        "username": f"user_{i}",
        "action": "STRESS_TEST"
    })

if i % 10 == 0:
    push_task({
        "username": f"user_{i}"
    })

end = time.time()

print(f"Inserted {TOTAL_JOB} jobs")
print(f"Push Time: {end - start:.2f} seconds")
