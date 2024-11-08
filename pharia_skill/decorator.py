import inspect
import traceback
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel

from .csi import Csi, WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal, Error_InvalidInput
from .wit.types import Err

UserInput = TypeVar("UserInput", bound=BaseModel)
UserOutput = TypeVar("UserOutput", bound=BaseModel)


def skill(
    func: Callable[[Csi, UserInput], UserOutput],
) -> Callable[[Csi, UserInput], UserOutput]:
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

        def output_schema(self) -> dict[str, Any]:
            return output_model.model_json_schema()

        def input_schema(self) -> dict[str, Any]:
            return input_model.model_json_schema()

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func
