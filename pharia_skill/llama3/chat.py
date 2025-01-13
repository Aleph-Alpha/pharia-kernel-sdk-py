from dataclasses import dataclass

from pharia_skill.csi import CompletionParams, Csi, FinishReason

from .assistant import AssistantMessage
from .request import ChatRequest


@dataclass
class ChatResponse:
    """Response from a chat request."""

    message: AssistantMessage
    finish_reason: FinishReason


def chat(csi: Csi, request: ChatRequest) -> ChatResponse:
    """Chat with a Llama model.

    Available tools can be specified as part of the `ChatRequest`. If the model decides
    to do a tool call, this will be available on the response:

    Example::

        # define parameters of the function as a pydantic model
        class ShipmentParams(BaseModel):
            order_id: str

        # define the tool
        tool = ToolDefinition(
            name="get_shipment_date",
            description="Get the shipment date for a specific order",
            parameters=ShipmentParams,
        )

        # construct the `ChatRequest` with the user question
        user = Message.user("When will my order (42) arrive?")
        request = ChatRequest(llama, [user], [tool])

        # chat with the model
        response = llama3.chat(csi, request)

        # receive the tool call back
        assert response.message.tool_call is not None

        # execute the tool call (e.g. via http request)
        pass

        # construct the tool response
        tool_response = ToolResponse(tool.name, content="1970-01-01")

        request.provide_tool_response(tool_response)

        # chat with the model again
        response = llama3.chat(csi, request)


    After you have received the tool call response, you need to execute the tool call
    yourself. The result can be provided back to the model
    """
    # as we are doing a completion request, we need to construct the completion
    # params, which are slightly different from the chat request params
    completion_params = CompletionParams(
        return_special_tokens=True,
        max_tokens=request.params.max_tokens,
        temperature=request.params.temperature,
        top_p=request.params.top_p,
    )

    completion = csi.complete(request.model, request.render(), completion_params)
    message = AssistantMessage.from_raw_response(completion.text)

    request._extend(message)
    return ChatResponse(message, completion.finish_reason)
