import pytest

from pharia_skill.llama3 import (
    BuiltInTool,
    ChatRequest,
    ChatResponse,
    Message,
    Role,
    ToolCall,
    ToolDefinition,
)


def test_chat_request_to_prompt():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")

    chat_request = ChatRequest(messages=[system, user])

    prompt = chat_request.as_prompt()

    expected = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

oat milk<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    assert prompt == expected


def test_start_with_assistant():
    assistant = Message.assistant("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")

    with pytest.raises(ValueError):
        ChatRequest(messages=[assistant, user])


def test_end_with_assistant():
    user = Message.user("oat milk")
    assistant = Message.assistant("You are a poet who strictly speaks in haikus.")

    with pytest.raises(ValueError):
        ChatRequest(messages=[user, assistant])


def test_system_prompt_is_optional():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")
    assistant = Message.assistant("Hello!")
    ipython = Message.ipython("print('hello')")

    ChatRequest(messages=[user, assistant, ipython])
    ChatRequest(messages=[system, user, assistant, ipython])


def test_not_alternating_messages():
    user = Message.user("oat milk")
    ipython = Message.ipython("print('hello')")

    with pytest.raises(ValueError):
        ChatRequest(messages=[user, ipython])


def test_chat_response_from_reply():
    reply = "Hello tim!<|eot_id|>"
    chat_response = ChatResponse.from_reply(reply)

    assert chat_response.message.content == "Hello tim!"


def test_system_prompt_without_tools():
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[user])
    assert chat_request.system is None


def test_system_prompt_without_tools_from_user():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[system, user])
    assert chat_request.system is not None
    assert "poet" in chat_request.system.as_prompt()


def test_system_prompt_with_tools():
    tool = ToolDefinition(tool_name=BuiltInTool.CodeInterpreter)
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[user], tools=[tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.as_prompt() == expected


def test_system_prompt_merged_from_user_and_tools():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    tool = ToolDefinition(tool_name=BuiltInTool.CodeInterpreter)
    chat_request = ChatRequest(messages=[system, user], tools=[tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
You are a poet who strictly speaks in haikus.<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.as_prompt() == expected


def test_build_in_tools_are_listed():
    tools = [
        ToolDefinition(tool_name=BuiltInTool.CodeInterpreter),
        ToolDefinition(tool_name=BuiltInTool.BraveSearch),
        ToolDefinition(tool_name=BuiltInTool.WolframAlpha),
    ]
    chat_request = ChatRequest(
        messages=[Message.user("What is the square root of 16?")], tools=tools
    )
    assert chat_request.system is not None
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search, wolfram_alpha<|eot_id|>"""
    assert chat_request.system.as_prompt() == expected


def test_chat_response_from_reply_with_tool_call():
    reply = "<|python_tag|>def is_prime(n):\n   return True<|eom_id|>"
    chat_response = ChatResponse.from_reply(reply)

    assert chat_response.message.content is None
    assert len(chat_response.message.tool_calls) == 1
    tool_call = chat_response.message.tool_calls[0]
    assert tool_call.tool_name == BuiltInTool.CodeInterpreter
    assert tool_call.arguments == {"code": "def is_prime(n):\n   return True"}


def test_brave_search_call_is_parsed():
    reply = '\n\n<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    chat_response = ChatResponse.from_reply(reply)
    assert chat_response.message.content is None
    assert len(chat_response.message.tool_calls) == 1
    tool_call = chat_response.message.tool_calls[0]
    assert tool_call.tool_name == BuiltInTool.BraveSearch
    assert tool_call.arguments == {"query": "current weather in Menlo Park, California"}


def test_wolfram_alpha_call_is_parsed():
    reply = '<|python_tag|>wolfram_alpha.call(query="solve x^3 - 4x^2 + 6x - 24 = 0")<|eom_id|>'
    chat_response = ChatResponse.from_reply(reply)
    assert chat_response.message.content is None
    assert len(chat_response.message.tool_calls) == 1
    tool_call = chat_response.message.tool_calls[0]
    assert tool_call.tool_name == BuiltInTool.WolframAlpha
    assert tool_call.arguments == {"query": "solve x^3 - 4x^2 + 6x - 24 = 0"}


def test_code_interpreter_tool_call_as_prompt():
    tool_call = ToolCall(
        tool_name=BuiltInTool.CodeInterpreter,
        arguments={"code": "def is_prime(n):\n   return True"},
    )
    assert tool_call.as_prompt() == "def is_prime(n):\n   return True"


def test_brave_search_tool_call_as_prompt():
    tool_call = ToolCall(
        tool_name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    expected = 'brave_search.call(query="current weather in Menlo Park, California")'
    assert tool_call.as_prompt() == expected


def test_tool_call_message_as_prompt():
    tool_call = ToolCall(
        tool_name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    message = Message(role=Role.Assistant, content=None, tool_calls=[tool_call])
    expected = '<|start_header_id|>assistant<|end_header_id|>\n\n<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    assert message.as_prompt() == expected
