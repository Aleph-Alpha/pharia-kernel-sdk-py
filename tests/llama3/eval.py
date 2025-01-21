"""
Evaluate a model's ability to use tools.

With function calling, we take many prompt engineering assumptions:

1. Should the JSON based tools be defined in the system or user prompt?
2. Should a system prompt be provided (e.g. "You are a helpful assistant")?
3. What wording should be used to tell the models that it can use tools, but does not have to?

Therefore, the tool calling is evaluated against a small dataset. This dataset is made up of
two different types of items:

1. Items that require a tool call.
2. Items that do not require a tool call and where we know that a model without tools can achieve them.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from pydantic import ValidationError

from pharia_skill import Csi
from pharia_skill.llama3 import (
    AssistantMessage,
    BraveSearch,
    ChatRequest,
    CodeInterpreter,
    Tool,
    UserMessage,
)
from pharia_skill.llama3.request import to_completion_params
from pharia_skill.testing import DevCsi

model = "llama-3.3-70b-instruct"


@dataclass(frozen=True)
class Item:
    """An item in the dataset to evaluate the model against."""

    tools: list[type[Tool]]
    user: str
    expected: type[Tool] | Tool | str
    """The expectation we have of the model's output.

    If a type is provided, check the class.
    If a Tool is provided, check the instance.
    If a str is provided, check that answer contains the string.
    """


class Result(TypedDict):
    """Reporting result for evaluating a single item."""

    input: str
    tools: list[str]
    expected: str
    output: str
    success: bool


def step(csi: Csi, item: Item) -> Result:
    """Does the model do the expected thing?"""
    message = UserMessage(item.user)
    request = ChatRequest(model, [message], tools=item.tools)

    completion_params = to_completion_params(request.params)
    completion = csi.complete(model, request.render(), completion_params)
    try:
        # do not call `request.chat` here, as we want the save raw response in case
        # the tool parsing fails
        response = AssistantMessage.from_raw_response(completion.text, item.tools)
    except ValidationError:
        response = AssistantMessage(content=completion.text)

    result: Result = {
        "input": item.user,
        "tools": [tool.__name__ for tool in item.tools],
        "expected": "",
        "output": response.tool_calls[0].render()
        if response.tool_calls
        else str(response.content),
        "success": False,
    }

    # Check success based on expected output
    if isinstance(item.expected, str):
        result["expected"] = item.expected
        result["success"] = (
            response.content is not None and item.expected in response.content
        )
    elif isinstance(item.expected, type):
        result["expected"] = str(item.expected)
        result["success"] = response.tool_calls is not None and isinstance(
            response.tool_calls[0], item.expected
        )
    else:
        result["expected"] = item.expected.render()
        result["success"] = (
            response.tool_calls is not None
            and response.tool_calls[0].render() == item.expected.render()
        )
    return result


def accuracy(results: list[tuple[Result, bool]]) -> float:
    success_count = sum(result[0]["success"] for result in results)
    return round(success_count / len(results), 2)


def evaluate(csi: Csi, dataset: list[Item]) -> dict[str, float]:
    """Evaluate the model on all items in the dataset."""
    output_dir = Path(__file__).parent
    output_file = output_dir / "eval.json"

    results = [(step(csi, item), isinstance(item.expected, str)) for item in dataset]

    # Split the results into tool and no tool results
    tool_result = [result for result in results if not result[1]]
    no_tool_result = [result for result in results if result[1]]

    # Save results to JSON
    output = {
        "dataset": [result[0] for result in results],
        "accuracy": accuracy(results),
        "tool_accuracy": accuracy(tool_result),
        "no_tool_accuracy": accuracy(no_tool_result),
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)

    del output["dataset"]
    return cast(dict[str, float], output)


class GetGithubReadme(Tool):
    """Get the readme for a repository in the Aleph Alpha organization on GitHub."""

    repository: str


class GetShipmentDate(Tool):
    """Get the shipment date for an order."""

    order_id: int


class GetActiveOrders(Tool):
    """Get the active orders for multiple customers."""

    customers: list[int]


def dataset() -> list[Item]:
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
            tools=[GetActiveOrders],
            user="What are the active orders for the customers 1, 2, and 3?",
            expected=GetActiveOrders(customers=[1, 2, 3]),
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme, CodeInterpreter],
            user="Write code to compute the first ten Fibonacci numbers.",
            expected=CodeInterpreter,
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme, CodeInterpreter, BraveSearch],
            user="What is the weather in San Francisco right now?",
            expected=BraveSearch,
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme, CodeInterpreter],
            user="What is the meaning of life?",
            expected="life",
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="Can you draft me an application letter for a job at Aleph Alpha?",
            expected="Dear",
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="What is GitHub?",
            expected="developer",
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="Tell me a funny joke about a rabbit.",
            expected="rabbit",
        ),
        Item(
            tools=[GetShipmentDate, GetGithubReadme],
            user="What is the square root of 16?",
            expected="4",
        ),
    ]


if __name__ == "__main__":
    csi = DevCsi()
    result = evaluate(csi, dataset())
    print(result)
