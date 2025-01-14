from pharia_skill.llama3 import (
    AssistantMessage,
    BraveSearch,
    CodeInterpreter,
    Tool,
    ToolCall,
)


class GetGitHubReadme(Tool):
    pass


def test_tool_call_message_render():
    tool_call = ToolCall(
        "brave_search",
        BraveSearch(query="current weather in Menlo Park, California"),
    )
    message = AssistantMessage(tool_call=tool_call)
    expected = '<|start_header_id|>assistant<|end_header_id|>\n\n<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    assert message.render() == expected


def test_message_from_raw_response():
    response = "Hello tim!<|eot_id|>"
    message = AssistantMessage.from_raw_response(response)

    assert message.content == "Hello tim!"


def test_message_from_response_with_tool_call():
    response = "<|python_tag|>def is_prime(n):\n   return True<|eom_id|>"
    message = AssistantMessage.from_raw_response(response, tools=[CodeInterpreter])

    assert message.content is None
    assert message.tool_call is not None
    assert isinstance(message.tool_call, ToolCall)
    assert message.tool_call.name == "code_interpreter"
    assert isinstance(message.tool_call.arguments, CodeInterpreter)
    assert message.tool_call.arguments.src == "def is_prime(n):\n   return True"


def test_message_tool_call_without_python_tag():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = AssistantMessage.from_raw_response(response, tools=[GetGitHubReadme])
    assert message.content is None
    assert message.tool_call is not None
    assert message.tool_call.name == "get_github_readme"


def test_non_existing_tool_is_not_parsed():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = AssistantMessage.from_raw_response(response, tools=[])
    assert message.content is not None
    assert message.tool_call is None


def test_tool_call_from_chat_response_with_python_tag():
    response = """\n\n<|python_tag|>{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = AssistantMessage.from_raw_response(response, tools=[GetGitHubReadme])
    assert message.content is None
    assert message.tool_call is not None
    assert message.tool_call.name == "get_github_readme"


def test_render_assistant_message():
    message = AssistantMessage(content="Hello, world!")
    assert (
        message.render()
        == "<|start_header_id|>assistant<|end_header_id|>\n\nHello, world!<|eot_id|>"
    )
