from typing import Callable
from .wit import exports
from .wit.exports.skill_handler import Error_Internal
from .wit.imports import csi
from .wit.types import Err
import traceback


def skill(func: Callable) -> Callable:
    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                return func(csi, input)
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    func.__globals__["SkillHandler"] = SkillHandler
    return func
