import inspect
import json
import traceback
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel

from .csi import Csi, WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal, Error_InvalidInput
from .wit.types import Err

UserInput = TypeVar("UserInput", bound=BaseModel)


def skill(
    func: Callable[[Csi, UserInput], Any],
) -> Callable[[Csi, UserInput], Any]:
    signature = list(inspect.signature(func).parameters.values())

    assert len(signature) >= 2, "Skills must have exactly two arguments."

    if any([p.default is inspect.Parameter.empty for p in signature[2:]]):
        raise AssertionError(
            "All arguments after the second argument must have defaults."
        )

    models = [p.default for p in signature[2:]]

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
                return json.dumps(result).encode()
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

        def models(self) -> list[str]:
            return models

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func
