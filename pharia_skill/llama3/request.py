"""
The `ChatRequest` is the entire conversation state and its context.

It is initially constructed by the user by providing a user and potentially a
system message. Along with the model and completion parameters, also tools that
are available to the model (context) can be specified.

The `ChatRequest` can be extended from the LLM side by passing it to the
`chat` function. Afterwards, it can be extended from the user side by adding
a message or tool response to the request.
"""

from dataclasses import dataclass, field
from typing import Any, Sequence

from pydantic import field_serializer, field_validator

from pharia_skill.csi import ChatParams, CompletionParams, Csi, FinishReason

from .message import (
    AssistantMessage,
    Role,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from .response import SpecialTokens
from .tool import BuiltInTools, JsonSchema, ToolDefinition

Message = SystemMessage | UserMessage | AssistantMessage | ToolMessage


@dataclass
class ChatResponse:
    """Response from a chat request."""

    message: AssistantMessage
    finish_reason: FinishReason


@dataclass
class ChatRequest:
    """Represents the conversation state and context.

    Conversation history and available tools can be provided on initialization.
    Is automatically extended when passing it to the `chat` function.
    Can be reused for subsequent conversation turns by extending it with messages
    or tool results and passing it to the `chat` function again.
    """

    model: str
    messages: list[Message]
    tools: Sequence[ToolDefinition] = field(default_factory=list)
    params: ChatParams = field(default_factory=ChatParams)

    def __post_init__(self) -> None:
        validate_messages(self.messages)

    def chat(self, csi: Csi) -> ChatResponse:
        """Chat with a Llama model.

        Appends responses from the model to the conversation history.
        Available tools can be specified as part of the `ChatRequest`. If the model decides
        to do a tool call, this will be available on the response:

        Example::
            # define the tool
            class GetGithubReadme(BaseModel):
                repository: str

            # construct the `ChatRequest` with the user question
            user = Message.user("When will my order (42) arrive?")
            request = ChatRequest(llama, [user], tools=[GetGithubReadme])

            # chat with the model
            response = request.chat(csi)

            # receive the tool call back
            assert response.message.tool_call is not None

            # execute the tool call (e.g. via http request) and construct the tool response
            tool_response = ToolResponse(tool.name, content="1970-01-01")

            # extend the request and run a new chat
            request.extend(tool_response)
            response = request.chat(csi)
        """
        validate_messages(self.messages)

        # as we are doing a completion request, we need to construct the completion
        # params, which are slightly different from the chat request params
        completion_params = CompletionParams(
            return_special_tokens=True,
            max_tokens=self.params.max_tokens,
            temperature=self.params.temperature,
            top_p=self.params.top_p,
        )

        completion = csi.complete(self.model, self.render(), completion_params)
        message = AssistantMessage.from_raw_response(completion.text, self.tools)

        self.messages.append(message)
        return ChatResponse(message, completion.finish_reason)

    def extend(self, message: Message) -> None:
        """Add a message to a chat request.

        When conversations have multiple turns (e.g. with tool calling), the
        conversation can be extended by adding a message to the request.
        """
        validate_messages(self.messages + [message])
        self.messages.append(message)

    def render(self) -> str:
        """Convert the chat request to a prompt that can be passed to the model."""
        messages = self.messages

        system_prompt_needed = self.tools and self.messages[0].role != Role.System
        if system_prompt_needed:
            messages.insert(0, SystemMessage.empty())

        prompt = SpecialTokens.BeginOfText.value
        for message in messages:
            prompt += message.render(self.tools)

        prompt += Role.Assistant.render()
        prompt += "\n\n"
        return prompt

    @field_serializer("tools")
    def as_dict(
        self, tools: Sequence[ToolDefinition]
    ) -> list[dict[str, Any] | JsonSchema | str]:
        """Pydantic can not serialize type[BaseModel], so we serialize it manually.

        Error serializing to JSON: PydanticSerializationError
        """
        serialized: list[dict[str, Any] | JsonSchema | str] = []
        for tool in tools:
            if isinstance(tool, dict):
                serialized.append(tool)
            elif tool in BuiltInTools:
                serialized.append(tool.name())
            else:
                serialized.append(tool.json_schema())
        return serialized

    @field_validator("tools", mode="before")
    @classmethod
    def validate_tools(cls, value: Any) -> Sequence[ToolDefinition]:
        assert isinstance(value, list), "Tools must be a list"
        tools = []
        for tool in value:
            if isinstance(tool, str):
                known = next((b for b in BuiltInTools if tool == b.name()), None)
                if not known:
                    raise ValueError(f"Invalid built in tool: {tool}")
                tools.append(known)
            elif isinstance(tool, dict):
                tools.append(JsonSchema(**tool))  # type: ignore
        return tools


def validate_messages(messages: list[Message]) -> None:
    """Validate the order of messages in a chat request.

    We enforce a sensible Llama3 prompt (even though it might not be required by the model),
    to give the developer early feedback if he is using the chat request incorrectly.

    Rules:
        1. The first message must be a system or user message.
        2. The conversation excluding a potential system message must alternate between user/ipython and assistant.
        3. The last message must be a user or ipython message.
    """
    if not messages:
        raise ValueError("Messages cannot be empty")

    # 1. check that the first message is a system or user message
    if messages[0].role not in (Role.System, Role.User):
        raise ValueError("First message must be a system or user message")

    cursor = 1 if messages[0].role == Role.System else 0

    # 2. check alternating between user/tool and assistant
    for i, message in enumerate(messages[cursor:]):
        if i % 2 == 0:
            if message.role not in (Role.User, Role.IPython):
                raise ValueError("User messages must alternate with assistant messages")
        else:
            if message.role != Role.Assistant:
                raise ValueError("Assistant messages must alternate with user messages")

    # 3. check that the last message is a user/ipython message
    if messages[-1].role not in (Role.User, Role.IPython):
        raise ValueError("Last message must be a user or ipython message")
