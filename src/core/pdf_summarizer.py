import asyncio
import json
import queue
import threading

from queue import Queue
from typing import List

from core.pdf_document import PDFPage
from llm_completion.completion import CompletionPost, ChatMessage, llm_completion
from logger import info

from llm_completion.models import ModelInfo


__all__ = ['spawn_summarizer']

SUMMARIZER_BS = 2
SUMMARIZER_MODEL = "gemini-2.0-flash"
SUMMARIZER_N_NEXT_PAGES = 1


async def summarize_single_item(item: PDFPage, model_list: List[ModelInfo]):
    def create_page_message(page):
        return ChatMessage(role="user", content=[
            {"type": "text", "content": f"PDF document, page {page.data.page_num}"},
            {"type": "image_url", "image_url": f"data:application/pdf;base64,{page.data.b64_data}"}
        ])

    messages = [
        ChatMessage(role="system", content=""),
    ]
    if prev := item.prev:
        if not prev.has_unrecoverable_errors():
            messages.append(create_page_message(prev))

    messages.append(create_page_message(item))

    current = item
    for _ in range(SUMMARIZER_N_NEXT_PAGES):
        if next_ := current.next:
            if not next_.has_unrecoverable_errors():
                messages.append(create_page_message(next_))
            current = next_

    messages.append(ChatMessage(
        role="user",
        content=f"Summarize the page {item.data.page_num} in one brief sentence"
    ))

    post = CompletionPost(
        model=SUMMARIZER_MODEL,
        messages=messages,
        stream=False,
        max_tokens=8192
    )

    data = []
    stream = await llm_completion(post, model_list)
    async for chunk in stream:
        data.append(chunk)

    info(f"Page {item.data.page_num} Summary:\n {json.dumps(data, indent=4)}")



async def summarize_batch(items: List[PDFPage], model_list: List[ModelInfo]):
    await asyncio.gather(*[
        summarize_single_item(item, model_list) for item in items
    ])


def summarize_worker(
        q_in: Queue,
        q_out: Queue,
        stop_event: threading.Event,
        model_list: List[ModelInfo],
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while not stop_event.is_set():
            items: List[PDFPage] = []
            try:
                items.append(q_in.get(timeout=1.))

                for _ in range(SUMMARIZER_BS - 1):
                    try:
                        items.append(q_in.get_nowait())
                    except queue.Empty:
                        break

            except queue.Empty:
                continue

            if items:
                loop.run_until_complete(summarize_batch(items, model_list))
    finally:
        loop.close()

def spawn_summarizer(
        q_in: Queue,
        q_out: Queue,
        model_list: List[ModelInfo],
) -> threading.Event:
    stop_event = threading.Event()

    thread = threading.Thread(
        target=summarize_worker,
        args=(q_in, q_out, stop_event, model_list),
        daemon=True
    )

    thread.start()
    info("summarizer initialized")

    return stop_event
