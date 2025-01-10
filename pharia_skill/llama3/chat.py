from pharia_skill.csi import ChatParams, CompletionParams, Csi

from .message import ChatResponse
from .request import ChatRequest


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
    response = csi.complete(model, prompt, completion_params)
    return ChatResponse.from_text(response.text)
