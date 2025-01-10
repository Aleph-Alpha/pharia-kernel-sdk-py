from dataclasses import dataclass, field

from .message import Message, Role
from .response import SpecialTokens
from .tool import BuiltInTool, ToolDefinition


def validate_messages(messages: list[Message]) -> None:
    """Validate the order of messages in a chat request."""
    if not messages:
        raise ValueError("Messages cannot be empty")

    if messages[0].role not in (Role.System, Role.User):
        raise ValueError("First message must be a system or user message")

    cursor = 1 if messages[0].role == Role.System else 0

    # check that alternating between user/tool and assistant
    for i, message in enumerate(messages[cursor:]):
        if i % 2 == 0:
            if message.role not in (Role.User, Role.IPython):
                raise ValueError("User messages must alternate with assistant messages")
        else:
            if message.role != Role.Assistant:
                raise ValueError("Assistant messages must alternate with user messages")

    # check that the last message is a user/ipython message
    if messages[-1].role not in (Role.User, Role.IPython):
        raise ValueError("Last message must be a user or ipython message")


@dataclass
class ChatRequest:
    messages: list[Message]
    tools: list[ToolDefinition] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_messages(self.messages)

    def system_prompt_tools(self) -> list[ToolDefinition]:
        """Subset of specified tools that need to be activated in the system prompt.

        CodeInterpreter is automatically included when IPython is activated and does
        not need to be listed in the system prompt.
        """
        return [
            tool
            for tool in self.tools
            if tool.name in list(BuiltInTool)
            and tool.name != BuiltInTool.CodeInterpreter
        ]

    def user_provided_tools(self) -> list[ToolDefinition]:
        """Subset of specified tools that need to be injected into the user message."""
        return [tool for tool in self.tools if tool.name not in list(BuiltInTool)]

    @property
    def system(self) -> Message | None:
        """The system message that will be rendered.

        Conditionally activate the IPython environment if tools are provided.
        If built in tools are configured, they are listed in the system prompt.
        The code interpreter tools is automatically included when IPython is activated.
        Ensures that if the user has provided a system message himself, it is not overwritten.

        Reference: https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#input-prompt-format-2

        """
        if not self.tools:
            return self.messages[0] if self.messages[0].role == Role.System else None

        prompt = "Environment: ipython"
        if tools := self.system_prompt_tools():
            prompt += f"\nTools: {', '.join(tool.name for tool in tools)}"

        # include the original system prompt
        if self.messages[0].role == Role.System:
            prompt += f"\n{self.messages[0].content}"
        return Message.system(prompt)

    @property
    def user(self) -> Message:
        """The user message that will be rendered.

        User provided tools are injected into the user message and
        the model is encouraged to use the available tools.

        Reference: https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#input-prompt-format-5
        """
        provided = (
            self.messages[0] if self.messages[0].role == Role.User else self.messages[1]
        )
        assert provided.role == Role.User, "User message must be provided"

        if not self.user_provided_tools():
            return provided

        prompt = "Answer the user's question by making use of the following functions if needed.\n\n"
        for tool in self.user_provided_tools():
            prompt += f"{tool.render()}\n"

        prompt += "\nReturn function calls in JSON format."
        prompt += f"\n\nQuestion: {provided.content}"
        return Message.user(prompt)

    def messages_without_system_and_first_user(self) -> list[Message]:
        """The system and first user prompt are altered.

        This is the rest of the messages that don't need to be altered.
        """
        messages = [message for message in self.messages if message.role != Role.System]
        return messages[1:]

    def render(self) -> str:
        """Convert the chat request to a prompt"""
        prompt = SpecialTokens.BeginOfText.value
        prompt += self.system.render() if self.system else ""
        prompt += self.user.render()

        for message in self.messages_without_system_and_first_user():
            prompt += message.render()

        prompt += Role.Assistant.header
        prompt += "\n\n"
        return prompt
