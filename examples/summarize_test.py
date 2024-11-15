"""
An example of how to do a summarization
"""

import pytest

from pharia_skill import Csi
from pharia_skill.testing import DevCsi, StubCsi

from .summarize import Input, SummaryLength, summarize


@pytest.fixture
def csi() -> Csi:
    # you have to make sure that a Pharia Kernel instance is available
    return DevCsi()


@pytest.fixture
def attention_text() -> str:
    return """Attention Is All You Need"[1] is a 2017 landmark[2][3] research paper in machine learning authored by eight scientists working at Google. The paper introduced a new deep learning architecture known as the transformer, based on the attention mechanism proposed in 2014 by Bahdanau et al. It is considered a foundational[4] paper in modern artificial intelligence, as the transformer approach has become the main architecture of large language models like those based on GPT.[5][6] At the time, the focus of the research was on improving Seq2seq techniques for machine translation, but the authors go further in the paper, foreseeing the technique's potential for other tasks like question answering and what is now known as multimodal Generative AI.[1]

The paper's title is a reference to the song "All You Need Is Love" by the Beatles.[7] The name "Transformer" was picked because Uszkoreit liked the sound of that word.[8]

An early design document was titled "Transformers: Iterative Self-Attention and Processing for Various Tasks", and included an illustration of six characters from the Transformers animated show. The team was named Team Transformer.[7]

Some early examples that the team tried their Transformer architecture on included English-to-German translation, generating Wikipedia articles on "The Transformer", and parsing. These convinced the team that the Transformer is a general purpose language model, and not just good for translation.[8]

As of 2024, the paper has been cited more than 100,000 times.[9]

For their 100M-parameter Transformer model, they suggested learning rate should be linearly scaled up from 0 to maximal value for the first part of the training (i.e. 2% of the total number of training steps), and to use dropout, to stabilize training. "
"""


def test_summary_contains_expected_words_stub(attention_text: str):
    input = Input(text=attention_text, length=SummaryLength.SHORT)
    result = summarize(StubCsi(), input).root
    assert all(x in result.lower() for x in ("attention", "transformer"))


# you can remove that mark in your code, it is to prevent the test to run on github ci
@pytest.mark.kernel
def test_summary_contains_expected_words(csi: Csi, attention_text: str):
    input = Input(text=attention_text, length=SummaryLength.SHORT)
    result = summarize(csi, input).root

    assert all(x in result.lower() for x in ("attention", "transformer"))


# you can remove that mark in your code, it is to prevent the test to run on github ci
@pytest.mark.kernel
def test_summary_length(csi: Csi, attention_text: str):
    # When summarizing with different lengths
    input = Input(text=attention_text, length=SummaryLength.SHORT)
    short_summary = summarize(csi, input).root
    input = Input(text=attention_text, length=SummaryLength.LONG)
    long_summary = summarize(csi, input).root

    # Then the short summary should be shorter than the long summary
    assert len(short_summary) < len(long_summary)
