import inspect
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..csi import Csi
from ..decorator import Skill
from .dev import DevCsi


def with_csi() -> Csi:
    """The csi dependency that is injected so that it can be faked in tests."""
    return DevCsi()


def build_app(skill: Skill) -> FastAPI:
    """Build a FastAPI app instance that makes the skill available via HTTP.

    The skill is made available under the `/execute_skill` endpoint to mimic the
    Pharia Kernel API."""

    app = FastAPI()

    signature = list(inspect.signature(skill).parameters.values())
    SkillInput = signature[1].annotation

    class Input(BaseModel):
        input: SkillInput  # type: ignore
        skill: str

    @app.post("/execute_skill")
    async def execute_skill(csi: Annotated[Csi, Depends(with_csi)], input: Input):
        skill_name = input.skill.split("/")[-1]
        if not skill_name == skill.__name__:
            return JSONResponse(status_code=404, content={"detail": "Skill not found."})

        return JSONResponse(content=skill(csi, input.input))

    return app
