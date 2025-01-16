from pydantic import BaseModel

from pharia_skill import Csi, skill
from pharia_skill.llama3 import ChatRequest, CodeInterpreter, UserMessage, chat


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str
    executed_code: str | None
    code_result: str | None


@skill
def code(csi: Csi, input: Input) -> Output:
    """Optionally execute python code that the model has output"""
    message = UserMessage(content=input.question)
    request = ChatRequest(
        model="llama-3.3-70b-instruct", messages=[message], tools=[CodeInterpreter]
    )
    response = chat(csi, request)
    if not response.message.tool_calls:
        return Output(
            answer=str(response.message.content), executed_code=None, code_result=None
        )

    # we know that it will be code interpreter
    tool_call = response.message.tool_calls[0].arguments
    assert isinstance(tool_call, CodeInterpreter)

    tool_output = tool_call.run()
    request.extend(tool_output)

    # chat again, and return the output
    response = chat(csi, request)
    return Output(
        answer=str(response.message.content),
        executed_code=tool_call.src,
        code_result=tool_output.content,
    )
