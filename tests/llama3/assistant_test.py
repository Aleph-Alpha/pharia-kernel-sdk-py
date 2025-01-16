from pharia_skill.llama3 import (
    BraveSearch,
    CodeInterpreter,
    Tool,
    ToolCall,
    assistant,
)


class GetGitHubReadme(Tool):
    pass


def test_tool_call_message_render():
    tool_call = ToolCall(
        "brave_search",
        BraveSearch(query="current weather in Menlo Park, California"),
    )
    message = assistant.ToolRequest(tool_calls=[tool_call])
    expected = '<|start_header_id|>assistant<|end_header_id|>\n\n<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    assert message.render() == expected


def test_message_from_raw_response():
    response = "Hello tim!<|eot_id|>"
    message = assistant.from_raw_response(response)

    assert message.content == "Hello tim!"


def test_message_from_response_with_tool_call():
    response = "<|python_tag|>def is_prime(n):\n   return True<|eom_id|>"
    message = assistant.from_raw_response(response, tools=[CodeInterpreter])

    assert message.content is None
    assert message.tool_calls is not None
    first = message.tool_calls[0]
    assert isinstance(first, ToolCall)
    assert first.name == "code_interpreter"
    assert isinstance(first.arguments, CodeInterpreter)
    assert first.arguments.src == "def is_prime(n):\n   return True"


def test_message_tool_call_without_python_tag():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = assistant.from_raw_response(response, tools=[GetGitHubReadme])
    assert message.content is None
    assert message.tool_calls
    assert message.tool_calls[0].name == "get_github_readme"


def test_non_existing_tool_is_not_parsed():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = assistant.from_raw_response(response, tools=[])
    assert message.content is not None


def test_tool_call_from_chat_response_with_python_tag():
    response = """\n\n<|python_tag|>{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = assistant.from_raw_response(response, tools=[GetGitHubReadme])
    assert message.tool_calls
    assert message.tool_calls[0].name == "get_github_readme"


def test_render_assistant_message():
    message = assistant.AssistantReply(content="Hello, world!")
    assert (
        message.render()
        == "<|start_header_id|>assistant<|end_header_id|>\n\nHello, world!<|eot_id|>"
    )
