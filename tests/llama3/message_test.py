from pydantic import BaseModel

from pharia_skill.llama3.message import (
    AssistantMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from pharia_skill.llama3.tool import BraveSearch, CodeInterpreter, Tool, WolframAlpha
from pharia_skill.llama3.tool_call import ToolCall


class GetGithubReadme(Tool):
    """Get the readme of a GitHub repository"""

    repository: str


def test_render_system_message():
    system = SystemMessage("You are a helpful assistant.")
    expected = "<|start_header_id|>system<|end_header_id|>\n\nYou are a helpful assistant.<|eot_id|>"
    assert system.render(tools=[]) == expected


def test_system_prompt_tools():
    tools: list[type[Tool]] = [CodeInterpreter, BraveSearch, GetGithubReadme]
    assert SystemMessage.system_prompt_tools(tools) == [BraveSearch]


def test_system_prompt_with_tools():
    system = SystemMessage.empty()
    tools = [CodeInterpreter]
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
If you decide to run python code, assign the result to a variable called `result`.<|eot_id|>"""
    assert system.render(tools=tools) == expected


def test_system_prompt_merged_from_user_and_tools():
    system = SystemMessage("You are a poet who strictly speaks in haikus.")
    tools = [CodeInterpreter]
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
If you decide to run python code, assign the result to a variable called `result`.
You are a poet who strictly speaks in haikus.<|eot_id|>"""
    assert system.render(tools) == expected


def test_ipython_environment_activated_by_custom_tool():
    system = SystemMessage.empty()
    tools = [GetGithubReadme]
    expected = """<|start_header_id|>system<|end_header_id|>\n\nEnvironment: ipython<|eot_id|>"""
    assert system.render(tools) == expected


def test_system_prompt_lists_built_in_tools():
    tools: list[type[Tool]] = [CodeInterpreter, BraveSearch, WolframAlpha]
    system = SystemMessage.empty()
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search, wolfram_alpha
If you decide to run python code, assign the result to a variable called `result`.<|eot_id|>"""
    assert system.render(tools) == expected


def test_render_user_message():
    message = UserMessage("Hello, world!")
    expected = "<|start_header_id|>user<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render(tools=[]) == expected


def test_user_provided_tools():
    tools: list[type[Tool]] = [CodeInterpreter, BraveSearch, GetGithubReadme]
    assert UserMessage.json_based_tools(tools) == [GetGithubReadme]


def test_render_user_message_with_tools():
    message = UserMessage("What is the readme of the pharia-kernel repository?")
    tools: list[type[Tool]] = [GetGithubReadme, CodeInterpreter, BraveSearch]

    expected = """<|start_header_id|>user<|end_header_id|>

Answer the user's question by making use of the following functions if needed.

{
    "type": "function",
    "function": {
        "name": "get_github_readme",
        "description": "Get the readme of a GitHub repository",
        "parameters": {
            "properties": {
                "repository": {
                    "type": "string"
                }
            },
            "required": [
                "repository"
            ],
            "type": "object"
        }
    }
}

Return function calls in JSON format.

Question: What is the readme of the pharia-kernel repository?<|eot_id|>"""
    assert message.render(tools) == expected


def deserialize_user_and_system_message():
    # Given a pydantic model with a list of either a user or system message
    class Either(BaseModel):
        messages: list[UserMessage | SystemMessage]

    # When deserializing a system message
    data = [
        {
            "role": "system",
            "content": "Hello, world!",
        },
        {
            "role": "user",
            "content": "Hello, world!",
        },
        {
            "role": "system",
            "content": "Hello, world!",
        },
    ]
    messages = Either.model_validate(data).messages

    # Then the messages are deserialized correctly
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], UserMessage)
    assert isinstance(messages[2], SystemMessage)


def test_render_tool_response():
    tool = ToolMessage(
        content='{"weather": "sunny", "temperature": "70 degrees"}',
        success=True,
    )
    expected = '<|start_header_id|>ipython<|end_header_id|>\n\ncompleted[stdout]{"weather": "sunny", "temperature": "70 degrees"}[/stdout]<|eot_id|>'
    assert tool.render(tools=[]) == expected


def test_render_failed_tool_response():
    tool = ToolMessage(
        content="failed to connect to server",
        success=False,
    )
    expected = "<|start_header_id|>ipython<|end_header_id|>\n\nfailed[stderr]failed to connect to server[/stderr]<|eot_id|>"
    assert tool.render(tools=[]) == expected


def test_render_assistant_message_without_tool_calls():
    message = AssistantMessage("Hello, world!")
    expected = (
        "<|start_header_id|>assistant<|end_header_id|>\n\nHello, world!<|eot_id|>"
    )
    assert message.render(tools=[]) == expected


def test_render_assistant_messages_without_ipython_ends_in_eom():
    tool_call = ToolCall(
        name="get_github_readme", parameters=GetGithubReadme(repository="pharia-kernel")
    )
    message = AssistantMessage(tool_calls=[tool_call])
    expected = """<|start_header_id|>assistant<|end_header_id|>\n\n<|python_tag|>{"name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}<|eom_id|>"""
    assert message.render(tools=[GetGithubReadme]) == expected
