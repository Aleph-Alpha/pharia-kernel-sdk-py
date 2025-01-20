from typing import Any

from pydantic import BaseModel

from pharia_skill import Csi, skill
from pharia_skill.llama3 import ChatRequest, CodeInterpreter, ToolMessage, UserMessage


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str | None
    executed_code: str | None = None
    code_result: Any | None = None


@skill
def code(csi: Csi, input: Input) -> Output:
    """A skill that optionally executes python code to answer a question"""
    message = UserMessage(content=input.question)
    request = ChatRequest(
        model="llama-3.3-70b-instruct", messages=[message], tools=[CodeInterpreter]
    )
    response = request.chat(csi)
    if not response.message.tool_calls:
        return Output(answer=response.message.content)

    # we know that it will be code interpreter
    tool_call = response.message.tool_calls[0].parameters
    assert isinstance(tool_call, CodeInterpreter)

    output = tool_call.run()
    request.extend(ToolMessage(output))

    # chat again, and return the output
    response = request.chat(csi)
    return Output(
        answer=response.message.content,
        executed_code=tool_call.src,
        code_result=output,
    )
