import sys

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path


from core.logger import init_logger, info, error


__all__ = ["Args", "parse_args"]


@dataclass
class Args:
    target_dir: Path
    DEBUG: bool


def parse_args(base_dir: Path) -> Args:
    init_logger(True)
    parser = ArgumentParser()
    parser.add_argument("-d", "--target_dir", required=True, type=Path, help="Directory to watch for new files")
    parser.add_argument("--DEBUG", default=False, action="store_true")
    args = parser.parse_args()

    target_dir: Path = args.target_dir
    if not target_dir.is_absolute():
        target_dir = base_dir / target_dir
        info(f"target dir '{args.target_dir}' -> '{target_dir}' (completed to absolute path)")

    if not target_dir.is_dir():
        error(f"Target Directory '{target_dir}' does not exist")
        sys.exit(1)

    return Args(
        target_dir=target_dir,
        DEBUG=args.DEBUG
    )
