import queue

from queue import Queue

from core.args import parse_args
from core.fmt_output import format_output
from core.globals import BASE_DIR
from core.summarizer.step1 import create_ticket_step1, post_step1_heuristics, dump_step1_results
from core.summarizer.step2 import dump_step2_results, create_ticket_step2
from core.summarizer.summarizer import spawn_summarizer
from core.utils import clear_dump_files
from core.logger import init_logger, info, warn
from core.pdf_watchdog import spawn_watchdog
from core.pdf_processor import process_pdf, PDFDocument
from core.prompts import load_prompts

from llm_completion.models import get_model_list


def main():
    init_logger(True)
    args = parse_args(BASE_DIR)
    init_logger(args.DEBUG)
    info("logger initialized")
    clear_dump_files()

    process_q, summ_q = Queue(), Queue()
    documents = []

    model_list = get_model_list(BASE_DIR)
    prompts = load_prompts(BASE_DIR)

    w_stop_event = spawn_watchdog(process_q, args.target_dir)
    s_stop_event = spawn_summarizer(summ_q, model_list)

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
                if any([p.has_unrecoverable_errors() for p in doc]):
                    warn(f"Some pages in {doc.path.name} have unrecoverable errors. SKIPPING the document")
                    continue

                [summ_q.put(create_ticket_step1(page, prompts)) for page in doc]

                documents.append(doc)

            except queue.Empty:
                pass

            for doc in documents:
                if doc.step1_done() and not doc.step1_set:
                    post_step1_heuristics(doc)
                    dump_step1_results(doc)
                    doc.step1_set = True

                    sections = {p.data_step1.section_n for p in doc}
                    for s_n in sections:
                        page = [page for page in doc if page.data_step1.section_n == s_n][-1]
                        s_name = page.data_step1.sections[0]
                        ticket = create_ticket_step2(doc, prompts, s_n, s_name)
                        summ_q.put(ticket)

                if doc.step2_done():
                    dump_step2_results(doc)
                    documents.remove(doc)
                    info(f"Document {doc.path.name} was processed")
                    format_output(args.target_dir)

    except KeyboardInterrupt:
        info("Gracefully shutting down")
    finally:
        w_stop_event.set()
        s_stop_event.set()


if __name__ == "__main__":
    main()
