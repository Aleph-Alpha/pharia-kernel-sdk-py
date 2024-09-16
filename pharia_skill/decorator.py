from typing import Callable, Protocol
from .wit import exports
from .wit.exports.skill_handler import Error_Internal
from .wit.imports import csi
from .wit.imports.csi import (
    CompletionRequest,
    CompletionParams,
    Completion,
    ChunkParams,
    Language,
)
from .wit.types import Err
import traceback


class Csi(Protocol):
    @staticmethod
    def complete(model: str, prompt: str, params: CompletionParams) -> Completion: ...

    @staticmethod
    def chunk(text: str, params: ChunkParams) -> list[str]: ...

    @staticmethod
    def select_language(text: str, languages: list[Language]) -> Language | None: ...

    @staticmethod
    def complete_all(requests: list[CompletionRequest]) -> list[Completion]: ...


def skill(func: Callable) -> Callable:
    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                return func(csi, input)
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    assert "SkillHandler" not in func.__globals__, "`@skill` can only be used once."
    func.__globals__["SkillHandler"] = SkillHandler
    return func
