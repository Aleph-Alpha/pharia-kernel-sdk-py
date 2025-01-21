"""
Evaluate how well the function calling works.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from pydantic import ValidationError

from pharia_skill import CompletionParams, Csi
from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    SpecialTokens,
    Tool,
    UserMessage,
)
from pharia_skill.testing import DevCsi


class GetGithubReadme(Tool):
    """Get the readme for a repository in the Aleph Alpha organization on GitHub."""

    repository: str


class GetShipmentDate(Tool):
    """Get the shipment date for an order."""

    order_id: int


class GetActiveOrders(Tool):
    """Get the active orders for multiple customers."""

    customers: list[int]


model = "llama-3.1-8b-instruct"


@dataclass(frozen=True)
class Item:
    tools: list[type[Tool]]
    user: str
    # will check if the answer contains the string
    expected: Tool | str


class Result(TypedDict):
    input: str
    tools: list[str]
    expected: str
    output: str
    success: bool


def step(csi: Csi, item: Item) -> Result:
    """Does the model do the expected thing?"""
    message = UserMessage(item.user)
    request = ChatRequest(model, [message], tools=item.tools)
    try:
        # as we are doing a completion request, we need to construct the completion
        # params, which are slightly different from the chat request params
        completion_params = CompletionParams(
            return_special_tokens=True,
            max_tokens=request.params.max_tokens,
            temperature=request.params.temperature,
            top_p=request.params.top_p,
            stop=[SpecialTokens.StartHeader.value],
        )

        completion = csi.complete(model, request.render(), completion_params)
        response = AssistantMessage.from_raw_response(completion.text, item.tools)
    except ValidationError:
        response = AssistantMessage(content=completion.text)

    result: Result = {
        "input": item.user,
        "tools": [tool.__name__ for tool in item.tools],
        "expected": item.expected.render()
        if isinstance(item.expected, Tool)
        else item.expected,
        "output": response.tool_calls[0].render()
        if response.tool_calls
        else str(response.content),
        "success": False,
    }

    # Check success based on expected output
    if isinstance(item.expected, str):
        result["success"] = (
            response.content is not None and item.expected in response.content
        )
    else:
        result["success"] = (
            response.tool_calls is not None
            and response.tool_calls[0].render() == item.expected.render()
        )

    return result


def accuracy(csi: Csi, dataset: list[Item]) -> float:
    """Evaluate the model on all items in the dataset."""
    # Prepare output directory
    output_dir = Path(__file__).parent
    output_file = output_dir / "eval.json"

    # Run evaluation and collect results
    results = [step(csi, item) for item in dataset]

    # Calculate accuracy
    success_count = sum(result["success"] for result in results)
    accuracy_score = success_count / len(dataset)

    # Save results to JSON
    with open(output_file, "w") as f:
        json.dump(
            {"results": results, "accuracy": round(accuracy_score, 2)}, f, indent=4
        )

    return accuracy_score


def data() -> list[Item]:
    return [
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="When will the order 42 ship?",
            expected=GetShipmentDate(order_id=42),
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="What is the readme for the pharia-kernel repo?",
            expected=GetGithubReadme(repository="pharia-kernel"),
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="What is 3+3?",
            expected="6",
        ),
        Item(
            tools=[GetActiveOrders],
            user="What are the active orders for the customers 1, 2, and 3?",
            expected=GetActiveOrders(customers=[1, 2, 3]),
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="Tell me a funny joke about a rabbit and a carrot.",
            expected="carrot",
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="What is GitHub?",
            expected="developer",
        ),
    ]


if __name__ == "__main__":
    csi = DevCsi()
    result = accuracy(csi, data())

    print(f"Accuracy: {result:.2f}")
