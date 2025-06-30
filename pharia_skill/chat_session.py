from pharia_skill.csi import Csi, Message
from pharia_skill.csi.inference import ChatStreamResponse
from pharia_skill.csi.inference.tool import ToolCallRequest


class ChatSession:
    """A chat session manages a conversation with a model.

    The session is a higher level abstraction over the chat API, which might be useful
    in cases where multiple messages are exchanges with the model. A typical usage
    pattern would be:

    1. Start a conversation by `ChatSession.ask`.
    2. In case the model returns a tool call, you are responsible to execute the tool call
        yourself, and can report the result by calling `ChatSession.report_tool_result`.
        This will update the conversation and trigger another call to the model.
    3. In case the model returns a streaming message, you stream the result to the
        invoker of the Skill.
    """

    def __init__(
        self,
        csi: Csi,
        model: str,
        messages: list[Message],
        tools: list[str] | None = None,
    ):
        self.csi = csi
        self.model = model
        self.messages = messages
        self.tools = tools

    def _step(self) -> ChatStreamResponse:
        """Take a step in the chat interaction.

        Add a message to the conversation and trigger a new response from the model.
        """
        return self.csi.chat_stream(self.model, self.messages, tools=self.tools)

    def _handle_tool_call(self, tool_call: ToolCallRequest) -> None:
        """Handle a tool call from the model.

        The tool call is added to the conversation and the tool response is added to the conversation.
        """
        self.messages.append(tool_call._as_message())
        tool_response = self.csi.invoke_tool(tool_call.name, **tool_call.parameters)
        self.messages.append(tool_response._as_message())

    def run(self) -> ChatStreamResponse:
        """Run a chat session and execute tool calls until the model returns a normal response."""
        response = self._step()
        while True:
            if (tool_call := response.tool_call()) is not None:
                self._handle_tool_call(tool_call)
                response = self._step()
            else:
                return response
