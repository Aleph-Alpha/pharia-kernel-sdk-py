import inspect
import json
import traceback
from typing import Callable, Type, TypeVar

from pydantic import BaseModel

from .csi import Csi, WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal, Error_InvalidInput
from .wit.types import Err

UserInput = TypeVar("UserInput", bound=BaseModel)
UserOutput = TypeVar("UserOutput", bound=BaseModel | str | None)


def skill(
    func: Callable[[Csi, UserInput], UserOutput],
) -> Callable[[Csi, UserInput], UserOutput]:
    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 2, "Skills must have exactly two arguments."

    model: Type[UserInput] = signature[1].annotation
    assert issubclass(model, BaseModel), "The second argument must be a Pydantic model"

    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                validated = model.model_validate_json(input)
            except Exception:
                raise Err(Error_InvalidInput(traceback.format_exc()))
            try:
                result = func(WasiCsi(), validated)
                return as_json_str(result).encode()
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func


def as_json_str(value: BaseModel | str | None) -> str:
    match value:
        case None | str():
            return json.dumps(value)
        case BaseModel():
            return value.model_dump_json()
        case _:
            raise ValueError(f"Unsupported output type: {type(value)}")
