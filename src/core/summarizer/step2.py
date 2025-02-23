import json

from dataclasses import dataclass
from queue import Queue
from typing import List, Dict, Any

from core.globals import SUMMARIZER_MODEL, STEP2_DUMP_FILE, SUMMARIZER_FALLBACK_MODEL
from core.logger import warn
from core.pdf_document import PDFDocument, PDFDocumentDataItemStep2Part, PDFDocumentDataItemStep2
from core.prompts import Prompts
from core.summarizer.summ_utils import SummarizeTicket, create_page_message

from llm_completion.completion import ChatMessage, CompletionPayload
from llm_completion.models import ModelInfo, resolve_model_record


@dataclass
class SummarizeStep2Ticket(SummarizeTicket):
    section_n: int
    section: str


def pp(ticket: SummarizeStep2Ticket, res: List[Dict[str, Any]], q: Queue):
    r = res[0]
    ch0 = r["choices"][0]
    content = ch0["message"]["content"]

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
        err = f"Failed to parse answer. Error:\n{e}"
        messages = [
            ChatMessage(role="assistant", content=content),
            ChatMessage(role="user", content=f"{err}\nTry again, minding JSON format!")
        ]
        ticket.post.messages = messages
        ticket.post.model = SUMMARIZER_FALLBACK_MODEL
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

    post = CompletionPayload(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192,
        n=1,
        temperature=0.2
    )

    return SummarizeStep2Ticket(pp, post, doc, section_n, section)


def dump_step2_results(doc: PDFDocument, model_list: List[ModelInfo]):
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
        ],

        "usage": {
            "finished_in_s": round(doc.usage.ts_end - doc.usage.ts_start, 3),
            "calls": [
                {
                    "model_name": c.model_name,
                    "finished_in_s": round(c.ts_end - c.ts_start, 3),
                    "tokens_in": c.tokens_in,
                    "tokens_out": c.tokens_out,
                    "dollars_input": resolve_model_record(c.model_name, model_list).dollars_input,
                    "dollars_output": resolve_model_record(c.model_name, model_list).dollars_output,
                }
                for c in doc.usage.calls
            ]
        }

    }

    with STEP2_DUMP_FILE.open("a") as f:
        f.write(json.dumps(data) + "\n")
