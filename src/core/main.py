import sys
from argparse import ArgumentParser
from pathlib import Path

from logger import init_logger, info, error
from pdf_watchdog import start_watchdog


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def main():
    parser = ArgumentParser()
    parser.add_argument("-d", "--target_dir", required=True, type=Path, help="Directory to watch for new files")
    parser.add_argument("--DEBUG", default=False, action="store_true")
    args = parser.parse_args()

    init_logger(args.DEBUG)
    info("logger initialized")

    target_dir: Path = args.target_dir
    if not target_dir.is_absolute():
        target_dir = BASE_DIR / target_dir
        info(f"target dir '{args.target_dir}' -> '{target_dir}' (completed to absolute path)")

    if not target_dir.is_dir():
        error(f"Target Directory '{args.target_dir}' does not exist")
        sys.exit(1)

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
