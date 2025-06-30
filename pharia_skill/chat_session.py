from pharia_skill.csi import Csi, Message
from pharia_skill.csi.inference import ChatStreamResponse
from pharia_skill.csi.inference.tool import ToolOutput


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

    def _report_tool_result(self, tool_result: ToolOutput) -> ChatStreamResponse:
        """Report the result of a tool call that was executed back to the model.

        Return either a streaming response or a tool call request.
        """
        self.messages.append(tool_result._as_message())
        return self.csi.chat_stream(self.model, self.messages, tools=self.tools)

    def run(self) -> ChatStreamResponse:
        """Run a chat session and execute tool calls until the model returns a normal response."""
        response = self.csi.chat_stream(self.model, self.messages, tools=self.tools)
        while True:
            if (tool_call := response.tool_call()) is not None:
                self.messages.append(tool_call._as_message())
                tool_response = self.csi.invoke_tool(tool_call.name, **tool_call.parameters)
                response = self._report_tool_result(tool_response)
            else:
                return response
