from dataclasses import dataclass
from queue import Queue
from collections import Counter
from typing import Callable, List, Any, Dict

from core.pdf_document import PDFPage
from llm_completion.completion import CompletionPost, ChatMessage


@dataclass
class SummarizeTicket:
    pp: Callable[[Any, List[Dict[str, Any]], Queue], None]
    post: CompletionPost


def create_content_pdf(p: PDFPage) -> Dict[str, str]:
    return {"type": "image_url", "image_url": f"data:application/pdf;base64,{p.data.b64_data}"}


def create_page_message(p: PDFPage) -> ChatMessage:
    return ChatMessage(role="user", content=[
        {"type": "text", "content": f"PDF document page for the Context, page #{p.data.page_num}"},
        create_content_pdf(p)
    ])


def most_frequent(items: List[Any]) -> Any:
    if not items:
        return None

    str_items = [str(item) for item in items]
    most_common = Counter(str_items).most_common(1)[0][0]
    return eval(most_common)
