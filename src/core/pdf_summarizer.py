import threading
from queue import Queue

from logger import info


__all__ = ['spawn_summarizer']


def summarize_worker(q_in: Queue, q_out: Queue):
    pass


def spawn_summarizer(q_in: Queue, q_out: Queue):
    stop_event = threading.Event()

    thread = threading.Thread(
        target=summarize_worker,
        args=(q_in, q_out, stop_event),
        daemon=True
    )

    thread.start()
    info("summarizer initialized")
