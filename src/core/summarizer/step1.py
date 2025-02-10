import json
from dataclasses import dataclass
from queue import Queue
from typing import List, Dict, Any

from core.globals import SUMMARIZER_MODEL
from core.logger import error, warn
from core.pdf_document import PDFPage
from core.prompts import Prompts
from core.summarizer.summ_utils import SummarizeTicket, create_page_message
from llm_completion.completion import CompletionPost, ChatMessage


@dataclass
class SummarizeStep1Ticket(SummarizeTicket):
    page: PDFPage


def create_ticket_step1(
        page: PDFPage,
        prompts: Prompts,
        pages_before: int = 1, pages_after: int = 2
) -> SummarizeStep1Ticket:
    def pp(ticket: SummarizeStep1Ticket, res: List[Dict[str, Any]], q: Queue):
        r = res[0]
        ch0 = r["choices"][0]
        try:
            content = ch0["message"]["content"]
        except KeyError:
            error(f"couldn't get content from model response. Response:\n{ch0}")
            ticket.page.data_step1.attempts_left -= 1
            if ticket.page.data_step1.attempts_left:
                q.put(ticket)
            return

        try:
            d = json.loads(content)
            page_number = d["page_number"]
            sections = d["sections"]
            parts = d["parts"]

            assert page_number == page.data.page_num
            assert isinstance(sections, list)
            assert isinstance(parts, list)

        except Exception:
            warn(f"couldn't parse markdown sections and parts from model response. Response:\n{ch0}")
            q.put(ticket)
            return

        ticket.page.data_step1.sections = sections
        ticket.page.data_step1.parts = parts
        ticket.page.data_step1.success = True

    messages = [
        ChatMessage(role="system", content=prompts.SP_markdown_sections_and_parts),
    ]

    current = page
    for _ in range(pages_before):
        if not (current := current.prev):
            break
        messages.append(create_page_message(current))

    messages.append(create_page_message(page))

    current = page
    for _ in range(pages_after):
        if not (current := current.next):
            break
        messages.append(create_page_message(current))

    messages.append(ChatMessage(
        role="user",
        content=prompts.USER_markdown_sections_and_parts
        .replace("$PAGE_N$", str(page.data.page_num))
    ))

    post = CompletionPost(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192
    )

    return SummarizeStep1Ticket(pp, post, page)
