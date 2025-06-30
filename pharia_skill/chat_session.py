from collections.abc import Generator

from pharia_skill.csi import Csi, Message
from pharia_skill.csi.inference_types import MessageAppend
from pharia_skill.csi.tool import ToolCallRequest, ToolOutput


class ChatSession:
    """A chat session manages a conversation with a model.

    The session is a higher level abstraction over the chat API, which might be useful
    in cases where multiple messages are exchanges with the model. A typical usage
    pattern would be:

    1. Start a conversation by `ChatSession.chat`.
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
        system: str | None = None,
        tools: list[str] | None = None,
    ):
        self.csi = csi
        self.model = model
        self.messages: list[Message] = [Message.system(system)] if system else []
        self.tools = tools

    def ask(
        self, question: str
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        """Begin a chat interaction with the model.

        Return either a streaming response or a tool call request.
        """
        return self._step(Message.user(question))

    def report_tool_result(
        self, tool_result: ToolOutput
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        """Report the result of a tool call that was executed back to the model.

        Return either a streaming response or a tool call request.
        """
        return self._step(tool_result._as_message())

    def _step(
        self, message: Message
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        """Take a step in the chat interaction.

        Add a message to the conversation and trigger a new response from the model.
        """
        self.messages.append(message)
        response = self.csi.chat_stream(self.model, self.messages, tools=self.tools)
        stream = response.stream_with_tool()
        if isinstance(stream, ToolCallRequest):
            self.messages.append(stream._as_message())
            return stream
        else:
            return self._wrap_stream(stream)

    def _wrap_stream(
        self, stream: Generator[MessageAppend, None, None]
    ) -> Generator[MessageAppend, None, None]:
        """Adapt the stream such that is is stored on the session."""
        self.messages.append(Message.assistant(content=""))
        for append in stream:
            self.messages[-1].content += append.content
            yield append
