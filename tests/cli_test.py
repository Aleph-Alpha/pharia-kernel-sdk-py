from pharia_skill.cli import contains_class


def test_skill_handler_exists():
    assert contains_class("examples.haiku", "SkillHandler")
