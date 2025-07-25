import datetime as dt

import pytest
from pydantic import ValidationError

from pharia_skill.csi import Message, Role
from pharia_skill.csi.inference import MessageAppend
from pharia_skill.csi.inference.tool import (
    InvokeRequest,
    Tool,
    ToolCallRequest,
    _deserialize_tool_call,
    _remove_md_delimiters,
    _remove_md_prefix,
    _render_system,
    add_tools_to_system_prompt,
    could_be_tool_call,
    parse_tool_call,
)


def test_validation_of_invoke_request():
    InvokeRequest(name="add", arguments={"a": 1, "b": 2})


def test_nested_json_value():
    InvokeRequest(name="add", arguments={"a": [1, 2], "b": {"c": 3}})


def test_validation_error_for_invalid_json_value():
    # Given a class that is not JSON serializable
    class MyClass:
        pass

    # Then an error is raised when we try to put it in the arguments
    with pytest.raises(ValidationError):
        InvokeRequest(name="add", arguments={"a": 1, "b": {"c": MyClass()}})  # type: ignore


def test_add_tools_to_system_prompt_does_not_modify_messages():
    """Messages are handled by the user themselves.

    Even if we map tools to a different internal message representation, we should
    not alter their message state.
    """
    # Given a list of messages
    messages = [Message.user("Hello, world!")]

    # When adding the tools to the system prompt
    new_messages = add_tools_to_system_prompt(
        messages,
        [
            Tool(
                name="add",
                description="Add two numbers",
                input_schema={"a": {"type": "number"}, "b": {"type": "number"}},
            )
        ],
    )

    # Then the original messages are not modified
    assert messages == [Message.user("Hello, world!")]
    assert len(new_messages) == 2


def test_system_prompt_is_added_for_tools():
    # Given a list of messages without a system prompt
    messages = [Message.user("Hello, world!")]

    # When adding the tools to the system prompt
    tool = Tool(
        name="add",
        description="Add two numbers",
        input_schema={
            "properties": {
                "a": {"title": "A", "type": "integer"},
                "b": {"title": "B", "type": "integer"},
            },
            "required": ["a", "b"],
            "title": "addArguments",
            "type": "object",
        },
    )

    messages = add_tools_to_system_prompt(messages, [tool])

    # Then a system prompt messages is prepended containing the tools
    assert messages[0].role == Role.System


def test_existing_system_prompt_is_extended_for_tools():
    # Given a list of messages with a system prompt
    messages = [
        Message.system("You are a helpful assistant."),
        Message.user("Hello, world!"),
    ]

    # When adding the tools to the system prompt
    tool = Tool(
        name="add",
        description="Add two numbers",
        input_schema={"a": {"type": "number"}, "b": {"type": "number"}},
    )

    messages = add_tools_to_system_prompt(messages, [tool])
    assert len(messages) == 2


def test_no_tools_do_not_add_system_prompt():
    # Given a user message
    messages = [Message.user("Hello, world!")]

    # When adding a list of empty tools
    messages = add_tools_to_system_prompt(messages, [])

    # Then nothing has changed
    assert messages == [Message.user("Hello, world!")]


def test_no_tools_do_not_change_system_prompt():
    # Given a system prompt
    messages = [Message.system("You are Spider-Man."), Message.user("Hello, world!")]

    # When adding a list of empty tools
    messages = add_tools_to_system_prompt(messages, [])

    # Then nothing has changed
    assert messages == [
        Message.system("You are Spider-Man."),
        Message.user("Hello, world!"),
    ]


def test_tools_are_rendered_correctly_in_system_prompt():
    # Given an existing system prompt and a tool
    existing = "You are Spider-Man."
    tool = Tool(
        name="add",
        description="Add two numbers",
        input_schema={
            "properties": {
                "a": {"title": "A", "type": "integer"},
                "b": {"title": "B", "type": "integer"},
            },
            "required": ["a", "b"],
            "title": "addArguments",
            "type": "object",
        },
    )
    today = dt.date(2025, 6, 27)

    # When rendering the system prompt
    system = _render_system(today, [tool], existing)

    # Then the system prompt is rendered correctly
    expected = """Environment: ipython
Cutting Knowledge Date: December 2023
Today Date: 27 June 2025

Answer the user's question by making use of the following functions if needed.
Only use functions if they are relevant to the user's question.
Here is a list of functions in JSON format:
{\n    \"type\": \"function\",\n    \"function\": {\n        \"name\": \"add\",\n        \"description\": \"Add two numbers\",\n        \"parameters\": {\n            \"properties\": {\n                \"a\": {\n                    \"title\": \"A\",\n                    \"type\": \"integer\"\n                },\n                \"b\": {\n                    \"title\": \"B\",\n                    \"type\": \"integer\"\n                }\n            },\n            \"required\": [\n                \"a\",\n                \"b\"\n            ],\n            \"title\": \"addArguments\",\n            \"type\": \"object\"\n        }\n    }\n}

Return function calls in JSON format.

You are Spider-Man."""

    assert system == expected


def test_non_tool_calls_are_forwarded():
    # Given a stream of non-toolmessages
    items = [
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]

    # When parsing the tool calls
    tool_call = parse_tool_call(iter(items))

    # Then no tool call is returned
    assert tool_call is None


def test_tool_calls_are_yielded():
    # Given a stream of messages that contain a tool call
    function_parts = [
        '{"type": "function", "function": {"name": "search',
        '", "parameters": {"query": "2025 Giro de Italia last stage winning time"}}}',
    ]
    items = iter([MessageAppend(content=part, logprobs=[]) for part in function_parts])

    # When parsing the tool calls
    tool_call = parse_tool_call(iter(items))

    # Then the tool calls are yielded
    assert tool_call == ToolCallRequest(
        name="search",
        parameters={"query": "2025 Giro de Italia last stage winning time"},
    )


def test_empty_first_chunk_is_ignored():
    # Given a stream of messages that contain a tool call, but also an empty first chunk
    function_parts = [
        "",
        '{"type": "function", "function": {"name": "search',
        '", "parameters": {"query": "2025 Giro de Italia last stage winning time"}}}',
    ]
    items = iter([MessageAppend(content=part, logprobs=[]) for part in function_parts])

    # When streaming the tool calls
    tool_call = parse_tool_call(iter(items))

    # Then the tool calls are yielded
    assert tool_call == ToolCallRequest(
        name="search",
        parameters={"query": "2025 Giro de Italia last stage winning time"},
    )


def test_standard_tool_call_format_is_supported():
    # Given a function call in the standard format
    json = '{"type": "function", "function": {"name": "search", "parameters": {"query": "2025 Giro de Italia last stage winning time"}}}'

    # When deserializing the tool call
    deserialized = _deserialize_tool_call(json)

    # Then
    assert deserialized.name == "search"


def test_different_tool_format_is_supported():
    # Given a function call in the non-nested format
    json = '{"type": "function", "name": "search", "parameters": {"query": "2025 Giro de Italia last stage winning time"}}'

    # When deserializing the tool call
    deserialized = _deserialize_tool_call(json)

    # Then
    assert deserialized.name == "search"


def test_markdown_tool_call_is_supported():
    events = [
        MessageAppend(content="```json\n", logprobs=[]),
        MessageAppend(
            content='{"type": "function", "name": "query_knowledge_base", "parameters": {"query": "travel policy"}}',
            logprobs=[],
        ),
        MessageAppend(content="```", logprobs=[]),
    ]

    # When deserializing the tool call
    deserialized = parse_tool_call(iter(events))

    # Then
    assert deserialized is not None
    assert deserialized.name == "query_knowledge_base"
    assert deserialized.parameters == {"query": "travel policy"}


def test_one_tick_in_chunk_is_supported():
    events = [
        MessageAppend(content="`", logprobs=[]),
        MessageAppend(content="`", logprobs=[]),
        MessageAppend(content="`", logprobs=[]),
        MessageAppend(
            content='{"type": "function", "name": "query_knowledge_base", "parameters": {"query": "travel policy"}}',
            logprobs=[],
        ),
        MessageAppend(content="```", logprobs=[]),
    ]

    # When deserializing the tool call
    deserialized = parse_tool_call(iter(events))

    # Then
    assert deserialized is not None
    assert deserialized.name == "query_knowledge_base"
    assert deserialized.parameters == {"query": "travel policy"}


def test_could_be_tool_call_returns_true_if_content_starts_with_sequence():
    # Given a content string that starts with a sequence
    content = "`"

    # When checking if the content could be a tool call
    assert could_be_tool_call(content)


def test_could_be_tool_call_returns_true_if_sequence_starts_with_content():
    # Given a content string that starts with a sequence
    content = "```json\n{'function'"

    # When checking if the content could be a tool call
    assert could_be_tool_call(content)


def test_exact_match_also_returns_true():
    # Given a content string that starts with a sequence
    content = "```json\n{"

    # When checking if the content could be a tool call
    assert could_be_tool_call(content)


def test_no_match_returns_false():
    # Given a content string that does not start with a sequence
    content = "``json\n{"

    # When checking if the content could be a tool call
    assert not could_be_tool_call(content)


def test_removes_markdown_delimiters():
    # Given a content string that starts with a sequence
    content = "```json\n{"

    # When removing the markdown delimiters
    result = _remove_md_prefix(content)

    # Then the result is the content without the delimiters
    assert result == "{"


def test_trailing_markdown_delimiters_are_removed():
    # Given a content string that starts with a sequence
    content = "```json\n{}```"

    # When removing the markdown delimiters
    result = _remove_md_delimiters(content)

    # Then the result is the content without the delimiters
    assert result == "{}"
