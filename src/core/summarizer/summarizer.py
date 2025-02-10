import asyncio
import queue
import threading
from copy import copy

from queue import Queue
from typing import List, Iterable

from core.globals import SUMMARIZER_BS
from core.summarizer.summ_utils import SummarizeTicket
from llm_completion.completion import llm_completion
from core.logger import info

from llm_completion.models import ModelInfo


__all__ = ['spawn_summarizer']


async def process_ticket(q, ticket: SummarizeTicket, model_list: List[ModelInfo]):
    data = []
    stream = await llm_completion(ticket.post, model_list)
    async for chunk in stream:
        data.append(chunk)

    print(data)
    ticket.pp(ticket, data, q)


async def summarize_batch(q, items: Iterable[SummarizeTicket], model_list: List[ModelInfo]):
    await asyncio.gather(*[
        process_ticket(q, item, model_list) for item in items
    ])


def summarize_worker(
        q: Queue,
        stop_event: threading.Event,
        model_list: List[ModelInfo],
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while not stop_event.is_set():
            items = []
            try:
                items.append(q.get(timeout=1.))

                for _ in range(SUMMARIZER_BS - 1):
                    try:
                        items.append(q.get_nowait())
                    except queue.Empty:
                        break

            except queue.Empty:
                continue

            if items:
                loop.run_until_complete(summarize_batch(q, copy(items), model_list))
                items.clear()

    finally:
        loop.close()


def spawn_summarizer(
        q: Queue,
        model_list: List[ModelInfo],
) -> threading.Event:
    stop_event = threading.Event()

    thread = threading.Thread(
        target=summarize_worker,
        args=(q, stop_event, model_list),
        daemon=True
    )

    thread.start()
    info("summarizer initialized")

    return stop_event
