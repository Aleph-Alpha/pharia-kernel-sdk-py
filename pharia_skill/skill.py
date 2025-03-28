import inspect
import json
import traceback
from typing import Callable, Type, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import (
    BaseModel,
    # For generation of JSON schemas, Pydantic imports the `root_model` module at runtime: https://github.com/pydantic/pydantic/blob/main/pydantic/json_schema.py#L1500
    # As `componentize-py` resolves imports at build time, we are required to add this import here.
    RootModel,  # noqa: F401
)

from .bindings import exports
from .bindings.types import Err
from .csi import Csi
from .wit_csi import WitCsi

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
    # The import is inside the decorator to ensure the imports only run when the decorator is interpreted.
    # This is because we can only import them when targeting the `skill` world.
    # If we target the `message-stream-skill` world with a component and have the imports for the `skill` world
    # in this module at the top-level, we will get a build error in case this module is in the module graph.
    from .bindings.exports.skill_handler import (
        Error_Internal,
        Error_InvalidInput,
        SkillMetadata,
    )

    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 2, "Skills must have exactly two arguments."

    input_model: Type[UserInput] = signature[1].annotation
    assert issubclass(input_model, BaseModel), (
        "The second argument must be a Pydantic model"
    )

    assert func.__annotations__.get("return") is not None, (
        "The function must have a return type annotation"
    )
    output_model: Type[UserOutput] = func.__annotations__["return"]
    assert issubclass(output_model, BaseModel), (
        "The return type must be a Pydantic model"
    )

    # This code here inside the decorator (but outside of the `class SkillHandler`) is executed at build time.
    # In version 0.3 of the wit world, we did not account for the fact that the metadata method may return
    # an error. However, as pydantic does some imports at runtime, we need to take this possibility into account.
    # By calculating the metadata at build time, we can (in case there is an error) give the user direct feedback,
    # instead of failing at runtime.
    description = func.__doc__
    input_schema = json.dumps(input_model.model_json_schema()).encode()
    output_schema = json.dumps(output_model.model_json_schema()).encode()
    metadata = SkillMetadata(description, input_schema, output_schema)

    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                validated = input_model.model_validate_json(input)
            except Exception:
                raise Err(Error_InvalidInput(traceback.format_exc()))
            try:
                result = func(WitCsi(), validated)
                return result.model_dump_json().encode()
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

        def metadata(self) -> SkillMetadata:
            return metadata

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."

    def trace_skill(csi: Csi, input: UserInput) -> UserOutput:
        with trace.get_tracer(__name__).start_as_current_span(func.__name__) as span:
            span.set_attribute("input", json.dumps(input.model_dump()))
            result = func(csi, input)
            span.set_attribute("output", json.dumps(result.model_dump()))
            span.set_status(Status(StatusCode.OK))
            return result

    func.__globals__["SkillHandler"] = SkillHandler
    trace_skill.__globals__["SkillHandler"] = SkillHandler
    return trace_skill
