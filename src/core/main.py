import queue

from queue import Queue

from args import parse_args
from core.globals import BASE_DIR
from core.summarizer.step1 import create_ticket_step1
from core.summarizer.summarizer import spawn_summarizer
from logger import init_logger, info, warn
from pdf_watchdog import spawn_watchdog
from pdf_processor import process_pdf, PDFDocument
from prompts import load_prompts

from llm_completion.models import get_model_list


def main():
    init_logger(True)
    args = parse_args(BASE_DIR)
    init_logger(args.DEBUG)
    info("logger initialized")

    model_list = get_model_list(BASE_DIR)
    prompts = load_prompts(BASE_DIR)

    process_q, summ_q = Queue(), Queue()
    w_stop_event = spawn_watchdog(process_q, args.target_dir)
    s_stop_event = spawn_summarizer(summ_q, model_list)

    documents = []
    try:
        while True:
            try:
                file_path = process_q.get(timeout=0.5)
                doc = PDFDocument(file_path)
                info(f"processing PDF {doc.path.name} ...")
                process_pdf(doc)
                if doc.has_unrecoverable_errors():
                    warn(f"PDF {doc.path.name} has unrecoverable errors. SKIPPING")
                    continue

                [
                    summ_q.put(create_ticket_step1(page, prompts))
                    for page in doc
                ]

                documents.append(doc)

            except queue.Empty:
                pass

            for doc in documents:
                if doc.step1_done():
                    pass

                if doc.step2_done():
                    pass


    except KeyboardInterrupt:
        info("Gracefully shutting down")
    finally:
        w_stop_event.set()
        s_stop_event.set()


if __name__ == "__main__":
    main()
