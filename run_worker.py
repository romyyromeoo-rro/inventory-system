import multiprocessing
from worker import worker

NUM_WORKERS = 3


def start_worker():
    worker()

if __name__ == "__main__":
    processes = []

    for _ in range(NUM_WORKERS):
        p = multiprocessing.Process(
            target=start_worker
        )

        p.start()
        processes.append(p)

    for p in processes:
        p.join()
