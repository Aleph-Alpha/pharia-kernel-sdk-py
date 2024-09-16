import json
from typing import Callable
from .wit import exports
from .wit.exports.skill_handler import Error_Internal
from .wit.types import Err


def skill(func: Callable) -> Callable:
    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                return func(input)
            except Exception as exc:
                raise Err(Error_Internal(str(exc)))

    func.__globals__["SkillHandler"] = SkillHandler
    return func
