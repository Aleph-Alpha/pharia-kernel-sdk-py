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

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>""""
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

## Function Calling

The [llama3 module](https://pharia-skill.readthedocs.io/en/latest/references.html#module-pharia_skill.llama3), provides support for function calling. It supports both user defined and built-in tools.

### Tool Definition

You can define a tool by inheriting from the [Tool](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.Tool) class, which is a wrapper around a Pydantic base model.

For example, suppose we want to give our model the ability to get the readme of a github repository. We can define a tool like this:

```python
from pharia_skill.llama3 import Tool


class GetGithubReadme(Tool):
    """Get the readme of a github repository."""

    repository: str
```

You can provide default values for the arguments and even add a description for each field by using Pydantic's `Field` class:

```python
from pharia_skill.llama3 import Tool
from pydantic import Field

class GetGithubReadme(Tool):
    """Get the readme of a github repository."""

    repository: str = Field(
        description="The github repository to get the readme of.",
        default="https://github.com/aleph-alpha/pharia-kernel",
    )
```

The name of the tools is the `snake_case` version of the class name and the doc string is passed to the LLM to describe the tool.

### Tool Usage

You can pass all available tools to the LLM by using the `tools` argument of the [ChatRequest](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.ChatRequest) class.

```python
from pharia_skill.llama3 import ChatRequest, UserMessage

message = UserMessage(content="How do I install the kernel?")
request = ChatRequest(
    model="llama-3.1-8b-instruct",
    messages=[message],
    tools=[GetGithubReadme],
)
```

If the model decides to use a tool, it will reply with an [AssistantMessage](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.AssistantMessage) containing the tool call.
A [ToolCall](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.ToolCall) consists of the name of the tool and the parameters to pass to it. If you have provided the tool definition
as a Pydantic model, then the parameters field will be an instance of the model. In this way, you get a type-safe way to pass parameters to your tools.

Now, it is upon you to execute the tool call.
Once you have executed the tool, you can pass the result to the LLM by extending the [ChatRequest](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.ChatRequest.extend) with a [ToolMessage](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.ToolMessage).

You can then trigger another round of chat with the LLM to get the final result:

```python
from pharia_skill import Csi, skill
from pharia_skill.llama3 import ChatRequest, UserMessage, ToolMessage

@skill
def github_skill(csi: Csi, input: Input) -> Output:
    # The input has a question field, which we pass to the LLM
    message = UserMessage(content=input.question)
    request = ChatRequest(
        model="llama-3.3-70b-instruct",
        messages=[message],
        tools=[GetGithubReadme],
    )
    response = request.chat(csi)
    if not response.message.tool_calls:
        return Output(answer=str(response.message.content))

    tool_call = response.message.tool_calls[0].parameters
    assert isinstance(tool_call, GetGithubReadme)

    # execute the tool call
    readme = get_github_readme(tool_call.repository)

    # pass the result to the LLM
    request.extend(ToolMessage(readme))

    # chat again, and return the output
    response = request.chat(csi)
    return Output(answer=str(response.message.content))
```

Note that outbound http requests are currently not supported in the Kernel. This means tools that need to make http requests can only
be executed in a local environment with the [DevCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) class and not be deployed to the Kernel.

## Code Interpreter

The [CodeInterpreter](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.CodeInterpreter) tool is a built-in tool that allows the LLM to execute python code.
This tool is available in the [llama3 module](https://pharia-skill.readthedocs.io/en/latest/references.html#module-pharia_skill.llama3). Here is an example of how to use it:

```python
from pydantic import BaseModel
from pharia_skill import Csi, skill
from pharia_skill.llama3 import CodeInterpreter, ChatRequest, UserMessage, ToolMessage


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str | None
    executed_code: str | None = None
    code_result: Any | None = None


@skill
def code(csi: Csi, input: Input) -> Output:
    """A skill that optionally executes python code to answer a question"""
    message = UserMessage(content=input.question)
    request = ChatRequest(
        model="llama-3.3-70b-instruct", messages=[message], tools=[CodeInterpreter]
    )
    response = request.chat(csi)
    if not response.message.tool_calls:
        return Output(answer=response.message.content)

    # we know that it will be code interpreter
    tool_call = response.message.tool_calls[0].parameters
    assert isinstance(tool_call, CodeInterpreter)

    output = tool_call.run()
    request.extend(ToolMessage(output))

    # chat again, and return the output
    response = request.chat(csi)
    return Output(
        answer=response.message.content,
        executed_code=tool_call.src,
        code_result=output,
    )

```
