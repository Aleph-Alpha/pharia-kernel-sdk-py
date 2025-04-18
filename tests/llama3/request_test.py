import datetime as dt

from pydantic import BaseModel

from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    Tool,
    UserMessage,
)

llama = "llama-3.1-8b-instruct"


class GetGithubReadme(Tool):
    """Get the readme of a GitHub repository"""

    repository: str


def test_no_system_prompt_included_if_no_tools_provided():
    user = UserMessage("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user])
    assert "system" not in chat_request.render()


def test_system_prompt_included_if_only_custom_tools_provided():
    user = UserMessage("What is the square root of 16?")
    chat_request = ChatRequest(llama, [user], tools=[GetGithubReadme])
    assert "system" in chat_request.render()


def test_chat_request_to_prompt():
    system = "You are a poet who strictly speaks in haikus."
    user = UserMessage("oat milk")

    chat_request = ChatRequest(llama, [user], system=system)

    prompt = chat_request.render()

    expected = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

oat milk<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    assert prompt == expected


def test_custom_tool_definition_in_system_prompt():
    # Given a chat request with a custom tool definition
    chat_request = ChatRequest(
        llama,
        [UserMessage("What is the readme of the pharia-kernel repository?")],
        tools=[GetGithubReadme],
    )

    # When rendering the chat request
    rendered = chat_request.render()

    # Then the custom tool definition should be included in the system prompt
    expected = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Environment: ipython
Cutting Knowledge Date: December 2023
Today Date: {dt.datetime.now().strftime("%d %B %Y")}

Answer the user's question by making use of the following functions if needed.
Only use functions if they are relevant to the user's question.
Here is a list of functions in JSON format:
{{
    "type": "function",
    "function": {{
        "name": "get_github_readme",
        "description": "Get the readme of a GitHub repository",
        "parameters": {{
            "properties": {{
                "repository": {{
                    "type": "string"
                }}
            }},
            "required": [
                "repository"
            ],
            "type": "object"
        }}
    }}
}}

Return function calls in JSON format.

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What is the readme of the pharia-kernel repository?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"""
    assert rendered == expected


def test_chat_request_with_tool_definition_is_serializable():
    """Assert that a chat request is serializable.

    type[BaseModel] are not serializable by default, so this test
    ensures custom serialization of the `tools` attribute does not
    raise an error.
    """

    # Given an instance of a pydantic model with a chat request attribute
    class ChatApi(BaseModel):
        request: ChatRequest

    user = UserMessage("When will my order (42) arrive?")
    request = ChatRequest("llama-3.1-8b-instruct", [user], tools=[GetGithubReadme])
    chat = ChatApi(request=request)

    # Then the model can be dumped to json without an error
    chat.model_dump_json()


def test_tools_not_included_in_second_user_prompt():
    # Given a chat request with two user messages
    user = UserMessage("What is the meaning of life?")
    assistant = AssistantMessage("42")
    chat_request = ChatRequest(llama, [user, assistant, user], tools=[GetGithubReadme])

    # When rendering the chat request
    rendered = chat_request.render()

    # Then the tool definition is only included once
    assert rendered.count("github") == 1


def test_schema_includes_built_in_tools():
    # Given a wrapper class with a ChatRequest attribute
    class Wrapper(BaseModel):
        request: ChatRequest

    # When creating the schema
    schema = Wrapper.model_json_schema()

    # Then the tools are specified to either be "BuiltInToolSchema" or "JsonSchema"
    assert schema["$defs"]["ChatRequest"]["properties"]["tools"]["items"]["anyOf"] == [
        {"$ref": "#/$defs/JsonSchema"},
        {"$ref": "#/$defs/BuiltInToolSchema"},
    ]
