import json
import re
from typing import Any, Literal

from pydantic import BaseModel


class Tool(BaseModel):
    """Provide a tool definition as a Pydantic model.

    The name of the class will be used as function name. The description of the
    function is taken from the docstring of the class. The parameters are
    specified as attributes of the model. Type hints and default arguments can
    be used to specify the schema, and a description of a parameter can be added
    with the `Field` class.

    Example::

        from pydantic import BaseMode, Field

        class GetImageInformation(BaseModel):
            "Retrieve information about a specific image."

            registry: str
            repository: str = Field(
                description="The full identifier of the image in the registry",
            )
            tag: str = "latest"
    """

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """The (slightly incompliant) json schema of a tool.

        This schema is used in two ways:

        1. Passed to the model to define the tool
        2. For serialization to json as part of a chat request

        For all specified tools, this schema is passed to the model.
        LLama expects a json object with `type` "function" as the root elements
        and a `function` object with the keys `name`, `description`, and `parameters`.

        Only for the parameters, we can make use of the json schema representation of a
        pydantic models. Note that the output schema is invalid json schema, as there is
        no `function` type in the json schema specification:

        https://json-schema.org/draft/2020-12/json-schema-validation#section-6.1.1
        """
        schema = cls.model_json_schema()
        description = schema.get("description")
        if description is not None:
            del schema["description"]
        data = {
            "type": "function",
            "function": {
                "name": cls.name(),
                "description": description,
                "parameters": schema,
            },
        }
        cls._recursive_purge_title(data)
        return data

    @classmethod
    def name(cls) -> str:
        return cls._to_snake_case(cls.__name__)

    @classmethod
    def _to_snake_case(cls, name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @classmethod
    def _recursive_purge_title(cls, data: dict[str, Any]) -> None:
        """Remove the title field from a dictionary recursively.

        The title is automatically created based on the name of the pydantic model,
        but it is not shown in examples of the llama model card, hence we skip it.
        See https://github.com/pydantic/pydantic/discussions/8504 for more detail.
        """
        if isinstance(data, dict):
            for key in list(data.keys()):
                if key == "title" and "type" in data.keys():
                    del data[key]
                else:
                    cls._recursive_purge_title(data[key])

    def render(self) -> str:
        """Convert a tool call to prompt format again.

        When a tool call has been loaded from a model response, it is part of the
        conversation and needs to be converted back to a prompt when providing the
        full conversation history to the model for the next turn.
        """
        return json.dumps(
            {
                "name": self.name(),
                "parameters": self.model_dump(exclude_unset=True),
            }
        )


class Function(BaseModel):
    name: str
    parameters: dict[str, Any]
    description: str | None = None


class JsonSchema(BaseModel):
    """Provide a tool definition as a json schema.

    While `Tool` is a more user-friendly way to define a tool in
    code, in some cases it might put too many constraints on the user. E.g., it can
    not be serialized from a json http request. Therefore, function definitions can
    also be provided in the serialized, json schema format.
    """

    type: Literal["function"] = "function"
    function: Function

    def name(self) -> str:
        return self.function.name


ToolDefinition = type[Tool] | JsonSchema
"""A tool can either be defined as a Pydantic model or directly as a json schema."""


class CodeInterpreter(Tool):
    src: str

    def render(self) -> str:
        return self.src

    def run(self) -> Any:
        global_vars: dict[str, Any] = {}
        exec(self.src, global_vars)
        return global_vars.get("result")

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """Json representation of the code interpreter tool.

        This is not passed to the model, but only used for serialization to json
        as part of a chat request.
        """
        return {"type": "code_interpreter"}


class WolframAlpha(Tool):
    query: str

    def render(self) -> str:
        return f'wolfram_alpha.call(query="{self.query}")'

    @staticmethod
    def try_from_text(text: str) -> "WolframAlpha | None":
        if not text.startswith("wolfram_alpha.call"):
            return None
        try:
            query = text.split('wolfram_alpha.call(query="')[1].split('")')[0].strip()
            return WolframAlpha(query=query)
        except IndexError:
            return None

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """Json representation of the wolfram alpha tool.

        This is not passed to the model, but only used for serialization to json
        as part of a chat request.
        """
        return {"type": "wolfram_alpha"}


class BraveSearch(Tool):
    query: str

    def render(self) -> str:
        return f'brave_search.call(query="{self.query}")'

    @staticmethod
    def try_from_text(text: str) -> "BraveSearch | None":
        if not text.startswith("brave_search.call"):
            return None
        try:
            query = text.split('brave_search.call(query="')[1].split('")')[0].strip()
            return BraveSearch(query=query)
        except IndexError:
            return None

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """Json representation of the brave search tool.

        This is not passed to the model, but only used for serialization to json
        as part of a chat request.
        """
        return {"type": "brave_search"}


BuiltInTools: tuple[type[Tool], ...] = (CodeInterpreter, WolframAlpha, BraveSearch)
