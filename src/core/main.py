from argparse import ArgumentParser

from core.logger import init_logger, info


def main():
    parser = ArgumentParser()
    parser.add_argument("--DEBUG", default=False, action="store_true")
    args = parser.parse_args()

    init_logger(args.DEBUG)

    info("Hello from core!")


if __name__ == "__main__":
    main()
