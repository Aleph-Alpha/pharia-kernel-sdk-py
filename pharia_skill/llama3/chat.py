from dataclasses import dataclass

from pharia_skill.csi import ChatParams, Completion, CompletionParams, Csi, FinishReason

from .message import Message
from .request import ChatRequest


@dataclass
class ChatResponse:
    """Response from a chat request."""

    message: Message
    finish_reason: FinishReason

    @classmethod
    def from_completion(cls, completion: Completion) -> "ChatResponse":
        message = Message.from_raw_response(completion.text)
        return ChatResponse(message, completion.finish_reason)


def chat(
    csi: Csi, model: str, request: ChatRequest, params: ChatParams
) -> ChatResponse:
    """Chat abstractions for llama3 that allows tools calls.

    Tool definition can be provided as part of the request. If the model
    responds with a tool call (`IPython` role), the tool call will be
    parsed from the response. The resulting message will not have a content,
    but a `tool_call` attribute.
    """
    prompt = request.render()
    completion_params = CompletionParams(
        return_special_tokens=True,
        max_tokens=params.max_tokens,
        temperature=params.temperature,
        top_p=params.top_p,
    )
    completion = csi.complete(model, prompt, completion_params)
    return ChatResponse.from_completion(completion)
