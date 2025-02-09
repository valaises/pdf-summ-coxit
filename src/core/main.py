from pathlib import Path
from queue import Queue

from args import parse_args
from logger import init_logger, info
from pdf_watchdog import spawn_watchdog
from pdf_processor import process_pdf, PDFDocument
from pdf_summarizer import spawn_summarizer


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def main():
    init_logger(True)
    args = parse_args(BASE_DIR)
    init_logger(args.DEBUG)
    info("logger initialized")

    process_q = Queue()
    summ_q_in, summ_q_out = Queue(), Queue()
    w_stop_event = spawn_watchdog(process_q, args.target_dir)
    s_stop_event = spawn_summarizer(summ_q_in, summ_q_out)

    try:
        while True:
            file_path = process_q.get()
            doc = PDFDocument(file_path)
            info(f"processing PDF {doc.path.name} ...")
            process_pdf(doc)
            # todo: implement caching
    except KeyboardInterrupt:
        info("Gracefully shutting down")
    finally:
        w_stop_event.set()
        s_stop_event.set()


if __name__ == "__main__":
    main()
