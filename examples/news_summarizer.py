import json

from pydantic import BaseModel

from pharia_skill import Csi, InvokeRequest, Message, ToolOutput, skill


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    summary: str


@skill
def summarize(csi: Csi, input: Input) -> Output:
    """A skill that fetches and summarizes the latest news articles for the provided topic."""

    # Search for news articles
    search_news_output = csi.invoke_tool("search_news", query=input.topic)
    search_results = [json.loads(content) for content in search_news_output.contents]

    # Fetch the content of the news articles concurrently
    fetch_requests = [
        InvokeRequest(name="fetch", arguments={"url": result["url"]})
        for result in search_results
    ]
    fetch_outputs = csi.invoke_tool_concurrent(fetch_requests)

    # Format the news articles
    news = "\n\n\n".join(
        [
            f"Title: {result['title']}\nURL: {result['url']}\nDescription: {result['description']}\nContent: {output.text()}"
            for result, output in zip(search_results, fetch_outputs)
            if isinstance(output, ToolOutput)
        ]
    )

    # Summarize the news articles
    system = Message.system(
        "Summarize the latest news articles as a concise paragraph. Provide URL links in markdown format, i.e. [link](url)."
    )
    user = Message.user(
        f"""Here are the latest news articles about {input.topic}:
        {news}"""
    )
    answer = csi.chat("llama-3.3-70b-instruct", [system, user])
    assert answer.message.content is not None
    return Output(summary=answer.message.content.strip())
