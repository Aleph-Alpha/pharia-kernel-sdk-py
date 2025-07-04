"""
The protocol we offer to Skill developers.

This interface is type-checked, in that we validate all data that we pass along to the
bindings. For this validation, we rely on `pydantic.dataclasses` to validate the types.

Python uses duck typing and this implies that someone using a library is responsible to
ensure the types that are passed are correct. This assumption holds true for all types that
we use in the SDK, and do not pass on to the bindings. However, it is the responsibility of
the SDK to ensure that the error messages users receive if they pass incorrect types are
are actionable. With `componentize-py`, the backtrace which is offered does not guide the
user towards the correct solution. Therefore, it is our responsibility to make sure that
we pass the correct types to the bindings.

This validation responsibility only covers types we pass to the bindings, it does not extend
to assert the type of something we use in our Python code. E.g. if we receive a DocumentPath
in our `Csi` interface, and only use this to instantiate a `bindings.imports.DocumentPath`,
the Python interpreter makes sure the caller gets a good error message if they pass in e.g.
`None` and we access the `name` attribute in our SDK.
"""

from typing import Protocol, Sequence

from pydantic.types import JsonValue

from .chunking import Chunk, ChunkParams, ChunkRequest
from .document_index import (
    Document,
    DocumentPath,
    IndexPath,
    JsonSerializable,
    SearchFilter,
    SearchRequest,
    SearchResult,
)
from .inference import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    CompletionStreamResponse,
    ExplanationRequest,
    Granularity,
    InvokeRequest,
    Message,
    TextScore,
    Tool,
    ToolError,
    ToolOutput,
    ToolResult,
)
from .inference.tool import ToolCallRequest, add_tools_to_system_prompt
from .language import Language, SelectLanguageRequest


class Csi(Protocol):
    """The Cognitive System Interface (CSI) is a protocol that allows skills to interact with the Pharia Kernel.

    Most functionality in the CSI is offered in two forms: As a single request, and as multiple
    concurrent requests. For all concurrent requests, it is guaranteed that the responses are
    returned in the same order as the requests. Therefore, our interface requires the user to provide
    Sequences, as we want the input to be ordered.
    """

    def invoke_tool(self, name: str, **kwargs: JsonValue) -> ToolOutput:
        """Invoke a tool that is configured with the Kernel.

        Tools can be configured for each namespace by listing MCP servers in the namespace config.
        The Kernel then exposes the tools of these MCP servers to Skills.
        The list of available tools per namespace can be queried from the Kernel API.

        Parameters:
            name (str, required): Name of the tool to invoke.
            **kwargs (JsonValue, required): Arguments to pass to the tool.

        Raises:
            ToolError: If the tool invocation fails.
        """
        request = InvokeRequest(name, kwargs)
        result = self.invoke_tool_concurrent([request])[0]
        if isinstance(result, ToolOutput):
            return result
        else:
            raise ToolError(result.message)

    def invoke_tool_concurrent(
        self, requests: Sequence[InvokeRequest]
    ) -> list[ToolResult]:
        """Invoke multiple tools concurrently.

        This function does not raise an error if a tool invocation fails, but rather
        returns a `ToolResult`, which can either be a `ToolOutput` or a `ToolError`.
        The reason for this is that for concurrent tool invocations, raising an error
        would prevent the caller from accessing the results of other tool calls.

        Parameters:
            requests (list[InvokeRequest], required): List of invoke requests.
        """
        ...

    def list_tools(self) -> list[Tool]:
        """List all tools that are available to the skill.

        Returns:
            list[Tool]: List of tools.
        """
        ...

    def _list_tool_schemas(self, tools: list[str]) -> list[Tool]:
        """List all tool schemas that are specified in the tools parameter.

        This function raises an error if a tool is specified in the tools parameter but not
        available in the namespace.

        Returns:
            list[Tool]: List of tool schemas.
        """
        tool_schemas = {t.name: t for t in self.list_tools() if t.name in tools}
        for t in tools:
            if t not in tool_schemas:
                raise ValueError(
                    f"Tool {t} required by Skill but not configured in namespace."
                )
        return list(tool_schemas.values())

    def complete(
        self, model: str, prompt: str, params: CompletionParams | None = None
    ) -> Completion:
        """Complete a prompt using a specific model.

        Parameters:
            model (str, required): Name of model to use.
            prompt (str, required): The text to be completed. Prompts need to adhere
                to the format expected by the specified model.
            params (CompletionParams, optional, Default None):
                Parameters for the requested completion.

        Examples::

            prompt = f\"\"\"<|begin_of_text|><|start_header_id|>system<|end_header_id|>

            You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

            {input.root}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\"\"\"
            params = CompletionParams(max_tokens=64)
            completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
        """
        params = params or CompletionParams()
        request = CompletionRequest(model, prompt, params)
        return self.complete_concurrent([request])[0]

    def complete_concurrent(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        """Complete multiple prompts concurrently.

        This represents the concurrent version of :func:`~pharia_skill.Csi.complete`.

        Parameters:
            requests (list[CompletionRequest], required): List of completion requests.
        """
        ...

    def completion_stream(
        self, model: str, prompt: str, params: CompletionParams | None = None
    ) -> CompletionStreamResponse:
        """Complete a prompt using a specific model.

        This method represents the streaming version of :func:`~pharia_skill.Csi.complete`.
        Instead of returning a single completion, this method returns a
        :class:`~pharia_skill.CompletionStreamResponse`, allowing to receive the response
        in small chunks.

        Parameters:
            model (str, required): Name of model to use.
            prompt (str, required): The text to be completed.
            params (CompletionParams, optional, Default None):
                Parameters for the requested completion.
        """
        params = params or CompletionParams()
        return self._completion_stream(model, prompt, params)

    def _completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> CompletionStreamResponse: ...

    def chunk(self, text: str, params: ChunkParams) -> list[Chunk]:
        """Chunks a text into chunks according to params.

        Parameters:
            text (str, required): Text to be chunked.
            params (ChunkParams, required):
                Parameter used for chunking, model and maximal number of tokens.

        Examples::

            text = "A very very very long text that can be chunked."
            params = ChunkParams("llama-3.1-8b-instruct", max_tokens=5)
            result = csi.chunk(text, params)
            assert len(result) == 3
        """
        request = ChunkRequest(text, params)
        return self.chunk_concurrent([request])[0]

    def chunk_concurrent(self, requests: Sequence[ChunkRequest]) -> list[list[Chunk]]:
        """Chunk a text into chunks concurrently.

        Parameters:
            requests (list[ChunkRequest], required): List of chunk requests.
        """
        ...

    def chat(
        self, model: str, messages: list[Message], params: ChatParams | None = None
    ) -> ChatResponse:
        """Generate a model response from a list of messages comprising a conversation.

        Compared to completions, chat requests introduces the `messages` concept,
        abstracting away the details of model-specific prompt formats. A message
        represents a single natural language turn in a conversation.

        For more details, see <https://docs.aleph-alpha.com/products/apis/pharia-inference/chat-completions/>.

        Parameters:
            model (str, required):
                Name of model to use.

            messages (list[Message], required):
                List of messages, alternating between messages from user and assistant.

            params (ChatParams, optional, Default None):
                Parameters used for the chat.

        Examples::

            input = "oat milk"
            system = Message.system("You are a helpful assistant.")
            msg = Message.user("What is the capital of France?")
            model = "llama-3.1-8b-instruct"
            chat_response = csi.chat(model, [system, msg], ChatParams(max_tokens=64))
        """
        params = params or ChatParams()
        request = ChatRequest(model, messages, params)
        return self.chat_concurrent([request])[0]

    def chat_concurrent(self, requests: Sequence[ChatRequest]) -> list[ChatResponse]:
        """Generate model responses for a list of chat requests concurrently.

        This represents the concurrent version of :func:`~pharia_skill.Csi.chat`

        Parameters:
            requests (list[ChatRequest], required): List of chat requests.
        """
        ...

    def chat_stream(
        self,
        model: str,
        messages: list[Message],
        params: ChatParams | None = None,
        tools: list[str] | None = None,
    ) -> ChatStreamResponse:
        """Chat with a model with automatic tool invocation.

        While `chat_stream_step` allows to pass in tools that are then available to the
        model, it leaves the responsibility of executing the tool call to the caller.
        This method goes one step further and automatically executes the tool call.
        If the tool call fails, the model is informed about the failure and can try to
        recover with a different approach. Once the model returns a non-tool message,
        it is returned to the caller.

        Parameters:
            model (str, required): Name of model to use.
            messages (list[Message], required):
                List of messages, alternating between messages from user and assistant.
            params (ChatParams, optional, Default None): Parameters used for the chat.
            tools (list[str], optional, Default None):
                List of tool names that are available to the model.
        """
        tool_schemas = self._list_tool_schemas(tools) if tools else None
        response = self.chat_stream_step(model, messages, params, tool_schemas)

        if tools:
            while (tool_call := response.tool_call()) is not None:
                self._handle_tool_call(tool_call, messages)
                response = self.chat_stream_step(model, messages, params, tool_schemas)

        return response

    def chat_stream_step(
        self,
        model: str,
        messages: list[Message],
        params: ChatParams | None = None,
        tools: list[Tool] | None = None,
    ) -> ChatStreamResponse:
        """Generate a model response from a list of messages comprising a conversation.

        This method represents the streaming version of :func:`~pharia_skill.Csi.chat`.
        Instead of returning a single message, this method returns a
        :class:`~pharia_skill.ChatStreamResponse`, allowing to receive the response in
        small chunks.

        Parameters:
            model (str, required): Name of model to use.

            messages (list[Message], required):
                List of messages, alternating between messages from user and assistant.

            params (ChatParams, optional, Default None): Parameters used for the chat.

            tools (list[Tool], optional, Default None):
                List of tool schemas that are available to the model. These tools are
                added to the system prompt and the responsibility for invoking the
                tool is left to the caller. If the response is a tool call, it can be
                checked via :meth:`~pharia_skill.ChatStreamResponse.tool_call`.
        """
        params = params or ChatParams()
        if tools:
            messages = add_tools_to_system_prompt(messages, tools)

        return self._chat_stream(model, messages, params)

    def _handle_tool_call(
        self, tool_call: ToolCallRequest, messages: list[Message]
    ) -> None:
        """Handle a tool call from the model.

        The tool call is added to the conversation and the tool response is added to the conversation.
        """
        messages.append(tool_call.as_message())
        try:
            tool_response = self.invoke_tool(tool_call.name, **tool_call.parameters)
            messages.append(tool_response.as_message())
        except ToolError as e:
            messages.append(
                Message.tool(f'failed[stderr]:{{"error": {e.message}}}[/stderr]')
            )

    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse: ...

    def explain(
        self,
        prompt: str,
        target: str,
        model: str,
        granularity: Granularity = Granularity.AUTO,
    ) -> list[TextScore]:
        """Request an explanation for the completion.

        Parameters:
            prompt (str, required): The prompt used for the completion.
            target (str, required): The completion text.
            model (str, required): The model used for the completion.
            granularity (Granularity, optional, Default Granularity.AUTO):
                Controls the length of the ranges which are explained.
        """
        request = ExplanationRequest(prompt, target, model, granularity)
        return self.explain_concurrent([request])[0]

    def explain_concurrent(
        self, requests: Sequence[ExplanationRequest]
    ) -> list[list[TextScore]]:
        """Request an explanation for the completion concurrently.

        Parameters:
            requests (list[ExplanationRequest], required): List of explanation requests.
        """
        ...

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        """Select the detected language for the provided input based on the list of
        possible languages.

        If no language matches, None is returned.

        Parameters:
            text (str, required): Text input.
            languages (list[Language], required):
                All languages that should be considered during detection.

        Examples::

            text = "Ich spreche Deutsch nur ein bisschen."
            languages = [Language.English, Language.German]
            result = csi.select_language(text, languages)
        """
        request = SelectLanguageRequest(text, languages)
        return self.select_language_concurrent([request])[0]

    def select_language_concurrent(
        self, requests: Sequence[SelectLanguageRequest]
    ) -> list[Language | None]:
        """Detect the language for multiple texts concurrently.

        Parameters:
            requests (list[SelectLanguageRequest], required):
                List of select language requests.
        """
        ...

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
        filters: list[SearchFilter] | None = None,
    ) -> list[SearchResult]:
        """Search an existing Index in the Document Index.

        Parameters:
            index_path (IndexPath, required):
                Index path in the Document Index to access.
            query (str, required): Text to be search for.
            max_results (int, optional, Default 1): Maximal number of results.
            min_score (float, optional, Default None):
                Minimal score for result to be included.
            filters (list[SearchFilter], optional, Default None):
                Filters to be applied to the search.

        Examples::

            index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
            query = "What is the population of Heidelberg?"
            result = csi.search(index_path, query)
            r0 = result[0]
            "Heidelberg" in r0.content, "Heidelberg" in r0.document_path.name # True, True
        """
        request = SearchRequest(
            index_path, query, max_results, min_score, filters or []
        )
        return self.search_concurrent([request])[0]

    def search_concurrent(
        self, requests: Sequence[SearchRequest]
    ) -> list[list[SearchResult]]:
        """Execute multiple search requests against the Document Index."""
        ...

    def document(self, document_path: DocumentPath) -> Document:
        """Fetch a document from the Document Index.

        Parameters:
            document_path (DocumentPath, required):
                The document path to get the document from.

        Examples::

            document_path = DocumentPath("f13", "wikipedia-de", "Heidelberg")
            document = csi.document(document_path)
            assert document.path == document_path
        """
        return self.documents([document_path])[0]

    def documents(self, document_paths: Sequence[DocumentPath]) -> list[Document]:
        """Fetch multiple documents from the Document Index.

        The documents are guaranteed to be returned in the same order as the document
        paths.

        Parameters:
            document_paths (list[DocumentPath], required):
                The document paths to get the documents from.
        """
        ...

    def document_metadata(self, document_path: DocumentPath) -> JsonSerializable:
        """Return the metadata of a document in the Document Index.

        Parameters:
            document_path (DocumentPath, required):
                The document path to get metadata from.
        """
        return self.documents_metadata([document_path])[0]

    def documents_metadata(
        self, document_paths: Sequence[DocumentPath]
    ) -> list[JsonSerializable]:
        """Return the metadata of multiple documents in the Document Index.

        The metadata is guaranteed to be returned in the same order as the document
        paths.

        Parameters:
            document_paths (list[DocumentPath], required):
                The document paths to get metadata from.
        """
        ...
