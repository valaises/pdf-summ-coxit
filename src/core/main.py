from pathlib import Path
from queue import Queue

from args import parse_args
from logger import init_logger, info
from pdf_watchdog import spawn_watchdog
from pdf_processor import process_pdf
from pdf_processor import PDFDocument

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def main():
    init_logger(True)
    args = parse_args(BASE_DIR)
    init_logger(args.DEBUG)
    info("logger initialized")

    q = Queue()
    w_stop_event = spawn_watchdog(q, args.target_dir)

    try:
        while True:
            file_path = q.get()
            doc = PDFDocument(file_path)
            info(f"processing {doc.path} ...")
            process_pdf(doc)
    except KeyboardInterrupt:
        info("Gracefully shutting down")
    finally:
        w_stop_event.set()


if __name__ == "__main__":
    main()
