import pytest

from pharia_skill.testing import DevCsi

from .news_summarizer import Input, Output, summarize


@pytest.mark.skip("Search and fetch tools are not always configured.")
def test_skill_summarizes_news():
    csi = DevCsi(namespace="playground", project="kernel-test")
    input = Input(topic="oat milk")

    result = summarize(csi, input)

    assert isinstance(result, Output)
    assert "oat milk" in result.summary
