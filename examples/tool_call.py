from pydantic import RootModel

from pharia_skill import Csi, skill


class Input(RootModel[int]):
    root: int


class Output(RootModel[int]):
    root: int


@skill
def compute(csi: Csi, input: Input) -> Output:
    """A skill that computes the answer based on the provided number.

    The Kernel service offers two native tools (`add` and `subtract`) for developers to
    test tool calling, without setting up MCP servers.
    The native tools need to be enabled for each namespace, but the Kernel service
    offers the `test-beta` namespace with the tools enabled.
    This skill demonstrates how to invoke the tools.
    """

    add_output = csi.invoke_tool(name="add", arguments={"a": input.root, "b": 100})
    sum = int(add_output.contents[0])

    subtract_output = csi.invoke_tool(name="subtract", arguments={"a": sum, "b": 60})
    answer = int(subtract_output.contents[0])

    return Output(root=answer)
