import inspect
import json
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

from .csi import Csi, WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal, Error_InvalidInput
from .wit.types import E


@dataclass
class Err(Generic[E], Exception):
    """Represents an error that occurred during the execution of a skill.

    For some exceptions like NotImplementedError, `traceback.format_exc()`
    does not work as it tries assigning th `__traceback__` attribute to
    `wit.types.Err`, which is a frozen dataclass and such raises
    a `dataclasses.FrozenInstanceError`. Therefore we introduce our own
    non-frozen `Err` class.
    """

    value: E


UserInput = TypeVar("UserInput", bound=BaseModel)
Skill = Callable[[Csi, UserInput], Any]


def skill(func: Skill) -> Skill:
    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 2, "Skills must have exactly two arguments."

    model = signature[1].annotation
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

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func
