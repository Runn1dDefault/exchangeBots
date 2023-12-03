import time
import queue
import threading
from typing import Callable


def waiting_threads(some_queue: queue.Queue) -> None:
    not_over_threads = []
    while not some_queue.empty():
        thread = some_queue.get()
        time.sleep(0.02)
        if thread.is_alive():
            if thread not in not_over_threads:
                not_over_threads.append(thread)
            continue
        some_queue.task_done()
    while not_over_threads:
        for thread in not_over_threads:
            if thread.is_alive():
                continue
            not_over_threads.remove(thread)
    time.sleep(1)


def run_thread(*args, callback: Callable, some_queue: queue.Queue, max_size: int) -> threading.Thread:
    thread = threading.Thread(target=callback, daemon=True, args=args if args else ())
    if some_queue.maxsize >= max_size:
        waiting_threads(some_queue)
    thread.start()
    some_queue.put(thread)
    return thread
