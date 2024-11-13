import inspect
import json
import traceback
from typing import Any, Callable, Type, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

from .csi import Csi
from .wasi_csi import WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal, Error_InvalidInput
from .wit.types import Err

UserInput = TypeVar("UserInput", bound=BaseModel)
UserOutput = TypeVar("UserOutput", bound=BaseModel)


def skill(
    func: Callable[[Csi, UserInput], UserOutput],
) -> Callable[[Csi, UserInput], UserOutput]:
    """Turn a function with a specific signature into a skill that can be deployed on Pharia Kernel.

    The decorated function must be typed. It must have exactly two input arguments. The first argument
    must be of type `Csi`. The second argument must be a Pydantic model. The type of the return value
    must also be a Pydantic model. Each module is expected to have only one function that is decorated
    with `skill`.

    Example::

        from pharia_skill import ChatParams, Csi, Message, skill
        from pydantic import BaseModel

        class Input(BaseModel):
            topic: str

        class Output(BaseModel):
            haiku: str

        @skill
        def run(csi: Csi, input: Input) -> Output:
            system = Message.system("You are a poet who strictly speaks in haikus.")
            user = Message.user(input.topic)
            params = ChatParams(max_tokens=64)
            response = csi.chat("llama-3.1-8b-instruct", [system, user], params)
            return Output(haiku=response.message.content.strip())
    """
    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 2, "Skills must have exactly two arguments."

    input_model: Type[UserInput] = signature[1].annotation
    assert issubclass(
        input_model, BaseModel
    ), "The second argument must be a Pydantic model"

    assert (
        func.__annotations__.get("return") is not None
    ), "The function must have a return type annotation"
    output_model: Type[UserOutput] = func.__annotations__["return"]
    assert issubclass(
        output_model, BaseModel
    ), "The return type must be a Pydantic model"

    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                validated = input_model.model_validate_json(input)
            except Exception:
                raise Err(Error_InvalidInput(traceback.format_exc()))
            try:
                result = func(WasiCsi(), validated)
                return result.model_dump_json().encode()
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

        def _output_schema(self) -> dict[str, Any]:
            return output_model.model_json_schema()

        def _input_schema(self) -> dict[str, Any]:
            return input_model.model_json_schema()

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."

    def trace_skill(csi: Csi, input: UserInput) -> UserOutput:
        with trace.get_tracer(__name__).start_as_current_span(func.__name__) as span:
            span.set_attribute("type", "TASK_SPAN")
            span.set_attribute("input", json.dumps(input.model_dump()))
            result = func(csi, input)
            span.set_attribute("output", json.dumps(result.model_dump()))
            span.set_status(Status(StatusCode.OK))
            return result

    func.__globals__["SkillHandler"] = SkillHandler
    trace_skill.__globals__["SkillHandler"] = SkillHandler
    return trace_skill
