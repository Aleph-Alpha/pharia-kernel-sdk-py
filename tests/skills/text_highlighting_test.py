"""
Given a question and a fitting text found via Rag, we want to generate an answer and highlight the relevant part of the text.
"""

from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.csi.inference import Completion, FinishReason, TextScore, TokenUsage
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
    model = "llama-3.1-8b-instruct"
    params = CompletionParams(max_tokens=64, return_special_tokens=False)
    completion = csi.complete(model, prompt, params)
    answer = completion.text

    explanations = csi._explain(prompt=prompt, target=answer, model=model)
    first_explanation = explanations[0]
    highlight_begin = first_explanation.start
    highlight_end = first_explanation.start + first_explanation.length

    return Output(
        answer=answer, highlight_begin=highlight_begin, highlight_end=highlight_end
    )


class TextHighlightingStubCsi(StubCsi):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        return Completion(
            text=" Extreme conditions.",
            finish_reason=FinishReason.STOP,
            logprobs=[],
            usage=TokenUsage(prompt=0, completion=0),
        )

    def _explain(self, prompt: str, target: str, model: str) -> list[TextScore]:
        return [TextScore(start=0, length=0, score=0.5)]


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
