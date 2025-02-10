import json
import re

from dataclasses import dataclass
from json import JSONDecodeError
from queue import Queue
from typing import List, Dict, Any

from core.globals import SUMMARIZER_MODEL
from core.logger import warn
from core.pdf_document import PDFPage
from core.prompts import Prompts
from core.summarizer.summ_utils import SummarizeTicket, create_page_message, most_frequent, create_content_pdf

from llm_completion.completion import CompletionPost, ChatMessage


__all__ = ["SummarizeStep1Ticket", "create_ticket_step1"]


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
            try:
                d = json.loads(content)
            except JSONDecodeError as e:
                print(f"JSONDecodeError: {e};\nResponse:\n{content}")
                raise e

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

    post = CompletionPost(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192,
        n=8, # WARNING: not all models support N > 1
    )

    return SummarizeStep1Ticket(pp, post, page)
