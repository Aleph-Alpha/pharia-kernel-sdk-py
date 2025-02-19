"""
Given a question and a fitting text found via Rag, we want to generate an answer and highlight the relevant part of the text.
"""

from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.csi.inference import Completion, FinishReason, TokenUsage
from pharia_skill.testing import StubCsi


class Input(BaseModel):
    question: str
    text: str


class Output(BaseModel):
    answer: str
    highlight_begin: int
    highlight_end: int


@skill
def highlighting(csi: Csi, input: Input) -> Output:
    prompt = f"""Question: {input.question}
Text: {input.text}
Answer:"""
    params = CompletionParams(max_tokens=64, return_special_tokens=False)
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    answer = completion.text

    return Output(answer=answer, highlight_begin=0, highlight_end=0)


class TextHighlightingStubCsi(StubCsi):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        return Completion(
            text=" Extreme conditions.",
            finish_reason=FinishReason.STOP,
            logprobs=[],
            usage=TokenUsage(prompt=0, completion=0),
        )


def test_run_text_highlighting_skill():
    input = Input(
        question="What is the ecosystem adapted to?",
        text="""Scientists at the European Southern Observatory announced a groundbreaking discovery today: microbial life detected in the water-rich atmosphere of Proxima Centauri b, our closest neighboring exoplanet.
The evidence, drawn from a unique spectral signature of organic compounds, hints at an ecosystem adapted to extreme conditions.
This finding, while not complex extraterrestrial life, significantly raises the prospects of life's commonality in the universe.
The international community is abuzz with plans for more focused research and potential interstellar missions.""",
    )
    csi = TextHighlightingStubCsi()
    output = highlighting(csi, input)

    assert output.answer == " Extreme conditions."
