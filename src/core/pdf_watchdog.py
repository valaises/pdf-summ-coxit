import time
import threading
from pathlib import Path
from queue import Queue
from typing import Iterator

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from logger import info


__all__ = ["spawn_watchdog"]

FILE_RULE = "*.pdf"


def scan_existing_files(directory: Path) -> Iterator[Path]:
    for file_path in directory.rglob(FILE_RULE):
        if file_path.is_file():
            yield file_path


class EventHandler(FileSystemEventHandler):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def on_created(self, event: FileSystemEvent) -> None:
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

    [q.put(f) for f in scan_existing_files(target_dir)]

    watchdog_thread = threading.Thread(
        target=watchdog_worker,
        args=(target_dir, q, stop_event),
        daemon=True
    )
    watchdog_thread.start()
    info("watchdog initialized")

    return stop_event
