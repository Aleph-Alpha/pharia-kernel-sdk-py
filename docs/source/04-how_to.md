# How-To

The Kernel SDK provides all the building blocks needed to create sophisticated AI applications.
If you want to include any dependencies in your Skill, have a look [here](03-core_concepts.md#wasm-component)

## Completion

The base building block of any AI framework is the ability to do completion requests:

```python
from pharia_skill import Csi, skill
from pydantic import BaseModel

# define Input & Output models
# ...

@skill
def complete(csi: Csi, input: Input) -> Output:
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(max_tokens=64)
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return Output(haiku=completion)
```

## RAG

Skills can access knowledge from external documents. You can query the DocumentIndex:

```python
from pharia_skill import Csi, IndexPath, skill

@skill
def rag(csi: Csi, input: Input) -> Output:
    # specify the index we query against
    index = IndexPath(
        namespace="my-team-namespace"
        collection="confluence",
        index="asym-256",
    )

    # search for the input topic in the confluence collection
    documents = csi.search(index, query=input.topic)
```

## Streaming

The SDK provides interfaces to receive chat and completion responses in chunks, and to return intermediate responses.
This allows building Skills that stream their output in small chunks, in contrast to only returning a single response.

### Message Stream

A message stream tries to model a conversation as a sequence of messages.
In a stream there is only one active message at a time.
You can write text to the message stream using a writer, which is passed into the Skill.
The Kernel takes care of translating the interactions with the writer into Server-Sent-Events.
Each message has a begin and an end, which can be indicated by [writer.begin_message](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.MessageWriter.begin_message) and [writer.end_message](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.MessageWriter.begin_message) respectively.
Between these, you can iteratively append text with [writer.append_to_message](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.MessageWriter.append_to_message)
When ending the message, you can provide an optional, arbitrary payload.

```python
writer.begin_message("assistant")
writer.append_to_message("Hello, ")
writer.append_to_message("world!")
writer.end_message(None)
```

### Requesting a Stream

To request a chat completion as a stream, you can use the [csi.chat_stream](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.Csi.chat_stream) context manager.
It returns a [ChatStreamResponse](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.ChatStreamResponse), which provides a `stream` method you can iterate over:

```python
params = ChatParams()
with csi.chat_stream(model, messages, params) as response:
    for event in response.stream():
        # e.g. writer.append_to_message(event.content)
        ...
```

The writer also provides a convenience method for returning a `ChatStreamResponse` directly:

```python
params = ChatParams()
with csi.chat_stream(model, messages, params) as response:
    writer.forward_response(response)
```

In case you want to stream a completion response (in contrast to a chat response), you can use [csi.completion_stream](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.Csi.completion_stream).

### Decorator

Skills that stream their output must be annotated with the [message_stream](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.message_stream) decorator.
They have some unique properties:

1. They take a second argument of type `MessageWriter`
2. They don't return anything
3. If you want to return a custom payload, use [writer.end_message](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.MessageWriter.end_message)

```python
from pharia_skill import ChatParams, Csi, Message, MessageWriter, message_stream

@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
    model = "llama-3.1-8b-instruct"
    messages = [
        Message.system("You are a poet who strictly speaks in haikus."),
        Message.user(input.topic),
    ]
    params = ChatParams()
    with csi.chat_stream(model, messages, params) as response:
        writer.forward_response(response)
```

Using the `message_stream` decorator requires passing the `--skill-type message-stream-skill` flag when running `pharia-skill build`.

## Conversational Search

Conversational search is the idea to have a chat conversation with an LLM which has access to a knowledge database.
To implement this, we first need a Skill that exposes a chat interface.

The [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat) is emerging as a standard to expose conversational interface of LLMs.
This API is also offered in the `Csi` with the `chat` method. Leveraging this, you can easily expose your own custom flavoured chat API as a Kernel Skill.
Note that you can return expose internal datatypes in the interface of you Skill as long as they are wrapped in a `Pydantic` model:

```python
from pharia_skill import Csi, Message, skill

class ChatInterface(BaseModel):
    """A chat input that is compatible with the OpenAI chat API."""

    message: list[Message]

@skill
def conversational_search(csi: Csi, input: ChatInterface) -> ChatInterface:
    # Alter the input message in any way to apply your own flavour
    # You could add a search lookup to allow conversational search, or just
    # prepend a custom system prompt
    input = do_search_lookup(input)
    output = csi.chat("llama-3.1-8b-instruct", input.messages)
    return ChatInterface(input.messages + [output.message])
```

You only need to define the `do_search_lookup` function and augment the incoming messages with some context.

## Tools

The Kernel and SDK offer support for function calling and tool invocations.
Details on how tools can be made available via MCP can be found in the [Tool Calling](03-core_concepts.md#tool-calling) section of the core concepts.

### Automatic Tool Calling

The [csi.chat_stream](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.Csi.chat_stream) supports automatic tool calling.
Tools are made available to the model by specifying their name as part of the request.
They are automatically added to the system prompt. In case the a custom system prompt is provided, these are merged by the SDK.

```python
with csi.chat_stream(model, messages, tools=["search", "fetch"]) as response:
    ...
```
The tool names are resolved to the correct schema by the SDK, as long as they are available ot the namespace.
In case the model requests a tool call, it is executed, and the response is fed back to the model.
This loop continues until the model returns a non-tool call response.
A typical usage pattern would be:

```python
from pydantic import BaseModel
from pharia_skill import Csi, Message, MessageWriter, message_stream


class Input(BaseModel):
    messages: list[Message]


@message_stream
def web_search(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
    model = "llama-3.3-70b-instruct"
    with csi.chat_stream(model, input.messages, tools=["search", "fetch"]) as response:
        writer.forward_response(response)
```


### Manual Tool Calling

The [csi.chat_stream_step](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.Csi.chat_stream_step) functions offers more granular control over the execution loop.
It allows specifying available tool schemas, but leaves the execution of the tool to the user.
A typical usage pattern might look like:

```python
from pydantic import BaseModel
from pharia_skill import Csi, Message, MessageWriter, message_stream


class Input(BaseModel):
    messages: list[Message]


@message_stream
def web_search(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
    messages = input.messages
    model = "llama-3.3-70b-instruct"

    # Retrieve the tool schemas from the csi
    tools = [t for t in csi.list_tools() if t.name in ("search", "fetch")]

    response = csi.chat_stream_step(model, messages, params, tools)
    while (tool_call := response.tool_call()) is not None:
        # add the tool call request to the conversation
        messages.append(tool_call.as_message())
        try:
            tool_response = self.invoke_tool(tool_call.name, **tool_call.parameters)
            # add the tool response to the conversation
            messages.append(tool_response.as_message())
        except ToolError as e:
            messages.append(
                Message.tool(f'failed[stderr]:{{"error": {e.message}}}[/stderr]')
            )
        response = self.chat_stream_step(model, messages, params, tool_schemas)

    writer.forward_response(response)
```

The [tool_call](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.ChatStreamResponse.tool_call) method allows to check if a response contains a tool calling.
It does not consume the stream for normal responses, so the last response to the end user will still be returned as a stream.

### Stream Events

For message stream skills, the Kernel reports tool call events via the SSE stream to the caller.
The caller will receive an event when a tool call starts and when a tool call finishes.