import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from pharia_skill import Completion, CompletionParams, Csi, skill
from pharia_skill.csi import FinishReason
from pharia_skill.testing.server import build_app, with_csi


@pytest.fixture(scope="module")
def client() -> TestClient:
    class Input(BaseModel):
        topic: str

    @skill
    def haiku(csi: Csi, input: Input) -> str:
        return csi.complete(
            "llama-3.1-8b-instruct",
            f"Write a haiku about {input.topic}",
            CompletionParams(),
        ).text

    app = build_app(haiku)

    class MockCsi(Csi):
        def complete(
            self, model: str, prompt: str, params: CompletionParams
        ) -> Completion:
            if prompt == "Write a haiku about oat milk":
                return Completion(
                    finish_reason=FinishReason.STOP, text="Oat milk, no sugar"
                )
            raise ValueError(f"Unexpected prompt: {prompt}")

    # override the csi dependency with a mock
    app.dependency_overrides[with_csi] = lambda: MockCsi()  # type: ignore

    return TestClient(app)


def test_skill_can_be_executed(client: TestClient):
    # When executing a skill against the app
    json = {"input": {"topic": "oat milk"}, "skill": "haiku"}
    response = client.post("/execute_skill", json=json)

    # Then the completion of the csi is returned
    assert response.status_code == 200
    assert response.json() == "Oat milk, no sugar"


def test_skill_with_namespace_can_be_executed(client: TestClient):
    # When executing a skill within a namespace
    json = {"input": {"topic": "oat milk"}, "skill": "playground/haiku"}
    response = client.post("/execute_skill", json=json)

    # Then the completion of the csi is returned
    assert response.status_code == 200
    assert response.json() == "Oat milk, no sugar"


def test_invalid_input_is_rejected(client: TestClient):
    # When executing a skill with invalid input
    json = {"input": {"invalid": "input"}, "skill": "haiku"}
    response = client.post("/execute_skill", json=json)

    # Then the skill is not executed
    assert response.status_code == 422


def test_unknown_skill_is_rejected(client: TestClient):
    # When executing an unknown skill
    json = {"input": {"topic": "oat milk"}, "skill": "unknown"}
    response = client.post("/execute_skill", json=json)

    # Then the skill is not executed
    assert response.status_code == 404


def test_skill_error_is_caught_and_exposed():
    # Given a skill that raises an error which is exposed by the app
    class Input(BaseModel):
        topic: str

    # delete SkillHandler from globals
    del globals()["SkillHandler"]

    @skill
    def haiku(csi: Csi, input: Input):
        raise ValueError("Something went wrong")

    app = build_app(haiku)

    # When the skill is executed
    json = {"input": {"topic": "oat milk"}, "skill": "haiku"}
    client = TestClient(app)
    response = client.post("/execute_skill", json=json)
    assert response.status_code == 500
    assert "Something went wrong" in response.json()
