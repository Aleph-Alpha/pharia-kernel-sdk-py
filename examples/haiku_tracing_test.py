"""
An example of how to test skill code with tracing.
"""

from pharia_skill.testing import DevCsi

from .haiku import Input, Output, haiku


def test_haiku_with_studio_tracing():
    # Set up the `DevCsi` with tracing enabled. This will create a new project in Studio if it doesn't exist.
    project = "kernel-test"
    csi = DevCsi.with_studio(project)

    # Run the skill
    input = Input(root="oat milk")
    result = haiku(csi, input)

    # You can flush the exporter manually, or it will be flushed when the `DevCsi` is garbage collected.
    csi.flush_exporter()

    # Assert the result is as expected
    assert isinstance(result, Output)
    assert "oat milk" in result.completion or "white" in result.completion
