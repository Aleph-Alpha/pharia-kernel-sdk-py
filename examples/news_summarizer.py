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
    assert isinstance(search_news_output, ToolOutput)

    # Extract the first 10 results
    search_results = [
        (result["title"], result["url"])
        for content in search_news_output.contents
        for result in json.loads(content)["results"][:10]
    ]

    # Fetch the content of the news articles concurrently
    fetch_requests = [
        InvokeRequest(name="fetch", arguments={"url": url}) for _, url in search_results
    ]
    fetch_outputs = csi.invoke_tool_concurrent(fetch_requests)

    # Format the news articles
    contents = [
        "\n\n".join(output.contents)
        for output in fetch_outputs
        if isinstance(output, ToolOutput)
    ]
    news = "\n\n\n".join(
        [
            f"Title: {title}\nURL: {url}\nContent: {content}"
            for (title, url), content in zip(search_results, contents)
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
    return Output(summary=answer.message.content.strip())
