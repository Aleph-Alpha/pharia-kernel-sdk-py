import pytest
from pydantic import BaseModel

from pharia_skill.llama3 import BuiltInTool, ChatRequest, Message, ToolDefinition


def test_system_prompt_without_tools():
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[user])
    assert chat_request.system is None


def test_chat_request_to_prompt():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")

    chat_request = ChatRequest(messages=[system, user])

    prompt = chat_request.render()

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


def test_system_prompt_without_tools_from_user():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[system, user])
    assert chat_request.system is not None
    assert "poet" in chat_request.system.render()


def test_system_prompt_with_tools():
    tool = ToolDefinition(name=BuiltInTool.CodeInterpreter)
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(messages=[user], tools=[tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.render() == expected


def test_system_prompt_merged_from_user_and_tools():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    tool = ToolDefinition(name=BuiltInTool.CodeInterpreter)
    chat_request = ChatRequest(messages=[system, user], tools=[tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
You are a poet who strictly speaks in haikus.<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.render() == expected


def test_ipython_environment_activated_with_custom_tool():
    tool = ToolDefinition(name="my-custom-tool")
    chat_request = ChatRequest(
        messages=[Message.user("What is the square root of 16?")], tools=[tool]
    )
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.render() == expected


def test_built_in_tools_are_listed():
    tools = [
        ToolDefinition(name=BuiltInTool.CodeInterpreter),
        ToolDefinition(name=BuiltInTool.BraveSearch),
        ToolDefinition(name=BuiltInTool.WolframAlpha),
    ]
    chat_request = ChatRequest(
        messages=[Message.user("What is the square root of 16?")], tools=tools
    )
    assert chat_request.system is not None
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search, wolfram_alpha<|eot_id|>"""
    assert chat_request.system.render() == expected


def test_custom_tool_definition_in_user_prompt():
    class Parameters(BaseModel):
        repository: str

    tool = ToolDefinition(
        name="get_github_readme",
        description="Get the readme of a GitHub repository",
        parameters=Parameters,
    )
    chat_request = ChatRequest(
        messages=[Message.user("What is the readme of the pharia-kernel repository?")],
        tools=[tool],
    )
    expected = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|><|start_header_id|>user<|end_header_id|>

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

Question: What is the readme of the pharia-kernel repository?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"""
    assert chat_request.render() == expected
