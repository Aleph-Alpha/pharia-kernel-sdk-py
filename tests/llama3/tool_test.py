from pydantic import Field

from pharia_skill.llama3 import BraveSearch, CodeInterpreter, Tool, WolframAlpha


class GetGithubReadme(Tool):
    """Get the readme of a GitHub repository"""

    repository: str = Field(
        description="The name of the GitHub repository to get the readme from",
    )
    registry: str = "default"


def test_pydantic_tool_definition_for_function():
    expected = {
        "type": "function",
        "function": {
            "name": "get_github_readme",
            "description": "Get the readme of a GitHub repository",
            "parameters": {
                "type": "object",
                "required": ["repository"],
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "The name of the GitHub repository to get the readme from",
                    },
                    "registry": {
                        "type": "string",
                        "default": "default",
                    },
                },
            },
        },
    }
    assert GetGithubReadme.json_schema() == expected


def test_run_code_interpreter():
    code = "def is_prime(n):\n    return True\n\nresult=is_prime(7)"
    tool = CodeInterpreter(src=code)
    result = tool.run()
    assert result is True


def test_wolfram_alpha_does_not_raise():
    mal_formatted = "wolfram_alpha.call(bad_query)"
    response = WolframAlpha.try_from_text(mal_formatted)
    assert response is None


def test_brave_search_does_not_raise():
    mal_formatted = "brave_search.call(bad_query)"
    response = BraveSearch.try_from_text(mal_formatted)
    assert response is None
