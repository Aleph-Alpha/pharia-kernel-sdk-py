from pydantic import Field

from pharia_skill.llama3 import Tool


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
