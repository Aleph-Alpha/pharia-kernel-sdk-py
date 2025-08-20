from pharia_skill import AgentInput, Csi, Message, MessageWriter, agent

DEVELOPER = """You are a helpful research assistant.
When tasked with a question, you will take as many steps and tries as needed to find the correct answer.
If you are doing a tool call, only respond with the tool call itself.
Do not respond with any reasoning or explanation in this case.

You can search the web and fetch content from URLs. Use markdown content when fetching URLs.
To ensure that efficiency, only fetch the content after you have found the relevant URLs."""


@agent
def web_search(csi: Csi, writer: MessageWriter[None], input: AgentInput) -> None:
    """A Skill that can decide to search the web."""

    model = "gpt-4o"
    messages = [Message.developer(DEVELOPER), *input.as_chat_messages()]
    with csi.chat_stream(model, messages, tools=["search", "scrape"]) as response:
        writer.forward_response(response)
