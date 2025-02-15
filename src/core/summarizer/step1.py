import json
import re

from dataclasses import dataclass
from queue import Queue
from typing import List, Dict, Any

from core.globals import SUMMARIZER_MODEL, STEP1_DUMP_FILE
from core.logger import warn
from core.pdf_document import PDFPage, PDFDocument
from core.prompts import Prompts
from core.summarizer.summ_utils import SummarizeTicket, create_page_message, most_frequent, create_content_pdf

from llm_completion.completion import CompletionPayload, ChatMessage


@dataclass
class SummarizeStep1Ticket(SummarizeTicket):
    page: PDFPage


def pp(ticket: SummarizeStep1Ticket, res: List[Dict[str, Any]], q: Queue):
    r = res[0]
    ch0 = r["choices"][0]

    errors = []

    page_number_all = []
    sections_all = []
    parts_all = []

    for ch in r["choices"]:
        try:
            content = ch["message"]["content"]
            content = content.replace("```json\n", "").replace("\n```", "")
            d = json.loads(content)

            ch_page_number = d["page_number"]
            ch_sections = d["sections"]
            ch_parts = d["parts"]

            page_number_all.append(ch_page_number)
            sections_all.append(ch_sections)
            parts_all.append(ch_parts)

        except Exception as e:
            errors.append(e)

    if len(errors) == len(r["choices"]) and not sections_all and not parts_all:
        text = f"couldn't parse markdown sections and parts from model response. Response:\n{ch0}\nErrors: {errors}"
        ticket.post.messages.append(
            ChatMessage(role="user", content=text)
        )
        warn(text)
        q.put(ticket)
        return

    _page_number = most_frequent(page_number_all)
    sections = most_frequent(sections_all)
    parts = most_frequent(parts_all)

    ticket.post.messages.append(
        ChatMessage(role="assistant", content=json.dumps(
            {"page_number": ticket.page.data.page_num, "sections": sections, "parts": parts}))
    )

    if len(sections) > 1:
        ticket.post.messages.append(
            ChatMessage(role="user", content="Error: there only could be 1 section in a page")
        )
        q.put(ticket)
        return

    if any(not re.match(r'^\d{6}$', str(s)) for s in sections):
        ticket.post.messages.append(
            ChatMessage(role="user", content="Error: section must be always a 6-digit number")
        )
        q.put(ticket)
        return

    if not isinstance(sections, list) or not isinstance(parts, list):
        ticket.post.messages.append(
            ChatMessage(role="user", content="Error: sections and parts must be lists")
        )
        q.put(ticket)
        return

    ticket.page.data_step1.sections = sections
    ticket.page.data_step1.parts = parts
    ticket.page.data_step1.success = True


def create_ticket_step1(
        doc: PDFDocument,
        page: PDFPage,
        prompts: Prompts,
        pages_before: int = 0, pages_after: int = 0
) -> SummarizeStep1Ticket:
    messages = [
        ChatMessage(role="system", content=prompts.SP_markdown_sections_and_parts),
    ]

    current = page
    for _ in range(pages_before):
        if not (current := current.prev):
            break
        messages.append(create_page_message(current))

    if pages_before and pages_after:
        messages.append(create_page_message(page))

    current = page
    for _ in range(pages_after):
        if not (current := current.next):
            break
        messages.append(create_page_message(current))

    messages.append(ChatMessage(
        role="user",
        content=[
            {"type": "text", "content": "target PDF page"},
            create_content_pdf(page),
        ]
    ))

    messages.append(ChatMessage(role="user", content=prompts.USER_markdown_sections_and_parts))

    post = CompletionPayload(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192,
        n=8, # WARNING: not all models support N > 1
        temperature=0.6,
    )

    return SummarizeStep1Ticket(pp, post, doc, page)


def post_step1_heuristics(doc: PDFDocument):
    for page in doc:
        if prev := page.prev:
            if prev.data_step1.sections != page.data_step1.sections:
                if any(re.search(r'part\s+(?:[2-9]|[1-9]\d+)', p, re.IGNORECASE) for p in page.data_step1.parts):
                    page.data_step1.sections = []

    for page in doc:
        page.data_step1.sections = list(set(page.data_step1.sections))
        page.data_step1.parts = list(set(page.data_step1.parts))

        if not page.data_step1.sections:
            if prev := page.prev:
                page.data_step1.sections = prev.data_step1.sections

    for page in doc:
        if (prev := page.prev) and (next_ := page.next):
            if set(prev.data_step1.sections) == set(next_.data_step1.sections) != set(page.data_step1.sections):
                page.data_step1.sections = prev.data_step1.sections

    section_n = 0
    for idx, page in enumerate(doc, 1):
        if idx == 1:
            pass

        elif any(re.search(r"part\s+1\b", p, re.IGNORECASE) for p in page.data_step1.parts):
            section_n += 1

        elif prev := page.prev:
            if prev.data_step1.sections != page.data_step1.sections:
                section_n += 1

        page.data_step1.section_n = section_n


def dump_step1_results(doc: PDFDocument):
    data = {
        "file_path": str(doc.path),
        "file_name": doc.path.name,
        "pages_cnt": doc.pages_cnt,
        "sections": list(set([p for page in doc for p in page.data_step1.sections])),
        "pages": [
            {
                "page_num": page.data.page_num,
                "sections": page.data_step1.sections,
                "section_n": page.data_step1.section_n,
            } for page in doc
        ]
    }

    with STEP1_DUMP_FILE.open("a") as f:
        f.write(json.dumps(data) + "\n")
