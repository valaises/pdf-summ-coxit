from dataclasses import dataclass
from typing import Callable

from core.pdf_document import PDFPage
from llm_completion.completion import CompletionPost, ChatMessage


@dataclass
class SummarizeTicket:
    pp: Callable
    post: CompletionPost


def create_page_message(p: PDFPage) -> ChatMessage:
    return ChatMessage(role="user", content=[
        {"type": "text", "content": f"PDF document, page {p.data.page_num}"},
        {"type": "image_url", "image_url": f"data:application/pdf;base64,{p.data.b64_data}"}
    ])
