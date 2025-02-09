from dataclasses import dataclass
from logging import info
from typing import List, Dict, Union, Any, Optional, AsyncIterator

import litellm

from core.logger import warn
from llm_completion.models import ModelInfo


__all__ = ["CompletionPost", "ChatMessage", "llm_completion"]


@dataclass
class ChatMessage:
    role: str
    content: Union[str, List[Any]]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        d = {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
        }
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls

        return d


@dataclass
class CompletionPost:
    model: str
    messages: List[ChatMessage]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    stream: bool = True

    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.2
    n: Optional[int] = 1
    top_p: Optional[float] = 1.0
    top_n: Optional[int] = 0
    stop: Optional[Union[str, List[str]]] = None


async def llm_completion(
    post: CompletionPost,
    model_list: List[ModelInfo],
) -> AsyncIterator[Dict[str, Any]]:
    messages: List[Dict] = [m.as_dict() for m in post.messages]
    model_record: Optional[ModelInfo] = next(model for model in model_list if model.name == post.model)
    if not model_record:
        raise ValueError(f"model {post.model} not found")

    if model_record.resolve_as not in litellm.model_list:
        warn(f"model {post.model} not in litellm.model_list")
    info(f"model resolve {model_record.name} -> {model_record.resolve_as}")

    response_streamer = litellm_completion_stream(
        model_record.resolve_as,
        messages,
        model_record,
        post,
    ) if post.stream else litellm_completion_not_stream(
        model_record.resolve_as,
        messages,
        model_record,
        post,
    )

    return response_streamer


async def litellm_completion_stream(
        model_name: str,
        messages: List[Dict],
        model_record: ModelInfo,
        post: CompletionPost,
) -> AsyncIterator[Dict[str, Any]]:
    try:
        stream = await litellm.acompletion(
            model=model_name, messages=messages, stream=True,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=min(model_record.max_output_tokens, post.max_tokens),
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=1,
        )

        finish_reason = None
        async for chunk in stream:
            try:
                data = chunk.model_dump()
                choice0 = data["choices"][0]
                finish_reason = choice0["finish_reason"]
            except Exception as e:
                warn(f"error in litellm_completion_stream: {e}")
                data = {"choices": [{"finish_reason": finish_reason}]}

            yield data

    except Exception as e:
        err_msg = f"error in litellm_completion_stream: {e}"
        warn(err_msg)
        yield {"choices": [{"error": err_msg}]}


async def litellm_completion_not_stream(
        model_name: str,
        messages: List[Dict],
        model_record: ModelInfo,
        post: CompletionPost
) -> AsyncIterator[Dict[str, Any]]:
    try:
        response = await litellm.acompletion(
            model=model_name, messages=messages, stream=False,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=min(model_record.max_output_tokens, post.max_tokens),
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=post.n,
        )
        response_dict = response.model_dump()
        yield response_dict

    except Exception as e:
        err_msg = f"error in litellm_completion_not_stream: {e}"
        warn(err_msg)
        yield {"error": err_msg}
