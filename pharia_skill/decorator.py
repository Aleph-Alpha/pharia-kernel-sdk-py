import traceback
from typing import Callable

from .csi import WasiCsi
from .wit import exports
from .wit.exports.skill_handler import Error_Internal
from .wit.types import Err


def skill(func: Callable) -> Callable:
    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                return func(WasiCsi, input)
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func
