from pydantic import BaseModel

from pharia_skill.llama3 import BuiltInTool, ChatRequest, Message, ToolDefinition

llama = "llama-3.1-8b-instruct"


def test_system_prompt_without_tools():
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user])
    assert chat_request.system is None


def test_chat_request_to_prompt():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")

    chat_request = ChatRequest(llama, [system, user])

    prompt = chat_request.render()

    expected = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

oat milk<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    assert prompt == expected


def test_system_prompt_without_tools_from_user():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(
        llama,
        [system, user],
    )
    assert chat_request.system is not None
    assert "poet" in chat_request.system.render()


def test_system_prompt_with_tools():
    tool = ToolDefinition(name=BuiltInTool.CodeInterpreter)
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user], [tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.render() == expected


def test_system_prompt_merged_from_user_and_tools():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("What is the square root of 16?")
    tool = ToolDefinition(name=BuiltInTool.CodeInterpreter)
    chat_request = ChatRequest(llama, [system, user], [tool])
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
You are a poet who strictly speaks in haikus.<|eot_id|>"""
    assert chat_request.system is not None
    assert chat_request.system.render() == expected


def test_ipython_environment_activated_with_custom_tool():
    tool = ToolDefinition(name="my-custom-tool")
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user], [tool])
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
    user = Message.user("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user], tools)
    assert chat_request.system is not None
    expected = """<|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search, wolfram_alpha<|eot_id|>"""
    assert chat_request.system.render() == expected


def test_custom_tool_definition_in_user_prompt():
    # Given a chat request with a custom tool definition
    class Parameters(BaseModel):
        repository: str

    tool = ToolDefinition(
        name="get_github_readme",
        description="Get the readme of a GitHub repository",
        parameters=Parameters,
    )
    chat_request = ChatRequest(
        llama,
        [Message.user("What is the readme of the pharia-kernel repository?")],
        [tool],
    )

    # When rendering the chat request
    rendered = chat_request.render()

    # Then the custom tool definition should be included in the user prompt
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
    assert rendered == expected
