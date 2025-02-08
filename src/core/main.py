from pathlib import Path

from args import parse_args
from logger import init_logger, info
from pdf_watchdog import start_watchdog


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def main():
    init_logger(True)
    args = parse_args(BASE_DIR)
    init_logger(args.DEBUG)
    info("logger initialized")

    q, stop_event = start_watchdog(args.target_dir)
    try:
        while True:
            file_path = q.get()
            info(f"processing {file_path}")
    except KeyboardInterrupt:
        info("Gracefully shutting down")
    finally:
        stop_event.set()

if __name__ == "__main__":
    main()
