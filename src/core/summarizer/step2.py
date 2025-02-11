import json

from dataclasses import dataclass
from queue import Queue
from typing import List, Dict, Any

from core.globals import SUMMARIZER_MODEL, STEP2_DUMP_FILE
from core.logger import warn
from core.pdf_document import PDFDocument, PDFDocumentDataItemStep2Part, PDFDocumentDataItemStep2
from core.prompts import Prompts
from core.summarizer.summ_utils import SummarizeTicket, create_page_message

from llm_completion.completion import ChatMessage, CompletionPost


@dataclass
class SummarizeStep2Ticket(SummarizeTicket):
    doc: PDFDocument
    section_n: int
    section: str


def pp(ticket: SummarizeStep2Ticket, res: List[Dict[str, Any]], q: Queue):
    r = res[0]
    ch0 = r["choices"][0]
    content = ch0["message"]["content"]

    ticket.post.messages.append(ChatMessage(role="assistant", content=content))

    try:
        content = content.replace("```json\n", "").replace("\n```", "")
        d = json.loads(content)
        section_summary = d["section_summary"]
        parts = d["parts"]
        parts = [
            PDFDocumentDataItemStep2Part(
                part_name=p["part_name"],
                part_summary=p["part_summary"],
            ) for p in parts
        ]
    except Exception as e:
        err = f"Failed to parse answer. Error: {e}"
        ticket.post.messages.append(
            ChatMessage(role="user", content=err)
        )
        warn(err)
        q.put(ticket)
        return

    ticket.doc.data_step2.append(
        PDFDocumentDataItemStep2(
            section=ticket.section,
            section_n=ticket.section_n,
            section_summary=section_summary,
            parts=parts,
        )
    )


def create_ticket_step2(
        doc: PDFDocument,
        prompts: Prompts,
        section_n: int,
        section: str,
) -> SummarizeStep2Ticket:
    pages_of_section = [p for p in doc if p.data_step1.section_n == section_n]
    assert pages_of_section

    messages = [
        ChatMessage(role="system", content=prompts.SP_summarize_section_and_parts)
    ]

    for p in pages_of_section:
        messages.append(
            create_page_message(p)
        )

    messages.append(
        ChatMessage(role="user", content=prompts.USER_summarize_section_and_parts)
    )

    post = CompletionPost(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192,
        n=1,
        temperature=0.2
    )

    return SummarizeStep2Ticket(pp, post, doc, section_n, section)


def dump_step2_results(doc: PDFDocument):
    data = {
        "file_path": str(doc.path),
        "file_name": doc.path.name,
        "pages_cnt": doc.pages_cnt,
        "summaries": [
            {
                "section": d.section,
                "section_n": d.section_n,
                "section_summary": d.section_summary,
                "parts": [
                    {
                        "part_name": p.part_name,
                        "part_summary": p.part_summary
                    }
                    for p in d.parts
                ]
            }
            for d in doc.data_step2
        ]
    }

    with STEP2_DUMP_FILE.open("a") as f:
        f.write(json.dumps(data) + "\n")
