# Building

The Kernel SDK provides all the building blocks needed to create sophisticated AI applications. In this section, we will show you how to use these components effectively. 

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

## Conversational Search

Conversational search is the idea to have a chat conversation with an LLM which has access to a knowledge database.
To implement this, we first need a skill that exposes a chat interface.

The [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat) is emerging as a standard to expose conversational interface of LLMs.
This API is also offered in the `Csi` with the `chat` method. Leveraging this, you can easily expose your own custom flavoured chat API as a Kernel Skill.
Note that you can return expose internal datatypes in the interface of you skill as long as they are wrapped in a `Pydantic` model:

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