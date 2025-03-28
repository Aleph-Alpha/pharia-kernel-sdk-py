"""
Two implementations of the Cognitive System Interface (CSI) that can be used for testing and development.

When Skills are run in the Kernel, the CSI is provided via an Application Binary Interface.
This interface is defined via the WASM Interface Type (WIT) language.
For development and debugging, Skills can also run in a local Python environment.
The CSI which is available to the Skill at runtime can be substituted with a DevCSI which is backed by HTTP requests against a running instance of the Kernel.
Developers can write tests, step through their Python code and inspect the state of variables.
"""

from .dev import DevCsi, MessageRecorder
from .stub import StubCsi

__all__ = ["StubCsi", "DevCsi", "MessageRecorder"]
