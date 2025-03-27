import importlib
import inspect


def inspect_wit_world(module_path: str) -> str:
    """Determine the world that a Skill should be build against.

    The SDK supports multiple wit worlds (e.g. `skill` and `message-stream-skill`).
    Each decorator targets a particular world.

    This function inspects a module, looking for one of the exported classes
    to determine which world the Skill should be build against.
    """
    if contains_class(module_path, "SkillHandler"):
        return "skill"
    elif contains_class(module_path, "MessageStream"):
        return "message-stream-skill"
    else:
        raise ValueError(
            f"Can not find a Skill in {module_path}. "
            "Did you add the @skill or @message_stream decorator to the Skill function?"
        )


def contains_class(module_path: str, class_name: str) -> bool:
    """Check if a class named `class_name` exists in the given module."""
    module = importlib.import_module(module_path)
    return any(
        name == "SkillHandler" and inspect.isclass(value)
        for name, value in vars(module).items()
    )


def test_skill_handler_exists():
    assert contains_class("examples.haiku", "SkillHandler")
