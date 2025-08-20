from typing import Callable, Literal

from pydantic import BaseModel

from pharia_skill.csi import Csi, Message

from .decorator import message_stream
from .writer import MessageWriter


class AgentMessage(BaseModel):
    role: Literal["user", "agent"]
    content: str

    def as_chat_message(self) -> Message:
        match self.role:
            case "user":
                return Message.user(self.content)
            case "agent":
                return Message.assistant(self.content)


class AgentInput(BaseModel):
    messages: list[AgentMessage]

    def as_chat_messages(self) -> list[Message]:
        return [m.as_chat_message() for m in self.messages]


AgentSkill = Callable[[Csi, MessageWriter[None], AgentInput], None]


def agent(func: AgentSkill) -> AgentSkill:
    """Define agents that can be deployed on Pharia Kernel.

    While the `message_stream` and `skill` decorator leave the developer some room to
    define the input and output of the skill, the `agent` decorator is more opinionated.
    By being more opinionated, we aim to (later) expose these agents via A2A from the
    Kernel. Before doing this, and propagating the concepts into the WIT world, we can
    already create value for developers by introducing a CLI based way to interact with
    these agents. In it's [core concepts](https://a2a-protocol.org/latest/topics/key-concepts/),
    A2A defines message and task concepts. While we are not ready to support the task
    concept in the Kernel, Agents can also be valuable without it.

    An example can be found [here](https://a2a-protocol.org/latest/specification/#92-basic-execution-synchronous-polling-style),
    where the agent responds quickly with a message, without creating a task. A2A
    supports both streaming and non-streaming responses, but we'll start with only
    streaming ones.
    """
    return message_stream(func)
