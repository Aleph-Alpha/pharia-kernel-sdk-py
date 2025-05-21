"""
A skill that can use function calling to search the web.
"""

from dataclasses import dataclass
from typing import Generator, Union

from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message, skill
from pharia_skill.llama3.message import ToolMessage, UserMessage
from pharia_skill.llama3.request import ChatRequest
from pharia_skill.llama3.tool_call import ToolCall


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str


@skill
def chat_with_tools(csi: Csi, input: Input) -> Output:
    request = ChatRequest(
        model="llama-3.3-70b-instruct",
        messages=[UserMessage(content=input.question)],
        params=ChatParams(),
        tools=["population_tool"],
    )
    for event in agent_step(csi, request):
        if isinstance(event, Message):
            return Output(answer=event.content)

    return Output(answer="No answer found.")


@dataclass
class ToolResultEvent:
    """Event indicating a tool has been executed and its result is available."""

    name: str
    content: str


StepEvent = Union[Message, ToolCall, ToolResultEvent]


def agent_step(
    csi: Csi, request: ChatRequest, max_steps: int = 10
) -> Generator[StepEvent, None, None]:
    """
    A generator that yields steps in a chat conversation involving tools.

    It yields one of three event types:
    1. ToolCall: When the LLM requests a tool to be called.
    2. ToolResultEvent: After a tool result is sent back to the generator,
                        this event confirms the result is being processed.
    3. Message: When the LLM provides a final answer.
    """
    response = request.chat(csi)
    step = 0
    while step < max_steps:
        step += 1
        if response.message.tool_calls:
            # Simplification, for now we are only handling one tool call at a time.
            tool_call = response.message.tool_calls[0]
            yield tool_call

            tool_result = csi.invoke_tool(tool_call.name, tool_call.parameters)
            yield ToolResultEvent(name=tool_call.name, content=tool_result)

            request.extend(ToolMessage(content=tool_result))
            response = request.chat(csi)
        elif response.message.content is not None:
            yield Message.assistant(content=response.message.content)
            return
        else:
            raise ValueError("LLM response must either have content or tool calls")
