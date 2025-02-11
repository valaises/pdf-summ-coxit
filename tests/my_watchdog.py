import threading
import time
from asyncio import Queue
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


FILE_RULE = "*.step1.jsonl"


class EventHandler(FileSystemEventHandler):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def on_modified(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)
        if path.match(FILE_RULE):
            self.queue.put(Path(event.src_path))


def watchdog_worker(target_dir: Path, queue: Queue, stop_event: threading.Event):
    event_handler = EventHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, str(target_dir), recursive=True)
    observer.start()
    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()

def spawn_watchdog(q: Queue, target_dir: Path) -> threading.Event:
    stop_event = threading.Event()

    watchdog_thread = threading.Thread(
        target=watchdog_worker,
        args=(target_dir, q, stop_event),
        daemon=True
    )
    watchdog_thread.start()
    print("watchdog initialized")

    return stop_event
