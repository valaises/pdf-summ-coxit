from dataclasses import dataclass
from typing import List, Dict, Union, Any, Optional, AsyncIterator

import litellm

from core.logger import warn
from llm_completion.models import ModelInfo


__all__ = ["CompletionPayload", "ChatMessage", "llm_completion"]


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
class CompletionPayload:
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
        model_list: List[ModelInfo],
        post: CompletionPayload
) -> AsyncIterator[Dict[str, Any]]:
    model_record: Optional[ModelInfo] = next(model for model in model_list if model.name == post.model)
    if not model_record:
        raise ValueError(f"model {post.model} not found")
    
    messages: List[Dict] = [m.as_dict() for m in post.messages]

    try:
        response = await litellm.acompletion(
            model=model_record.resolve_as, messages=messages, stream=False,
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
