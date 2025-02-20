"""
Given a question and a fitting text found via Rag, we want to generate an answer and highlight the relevant part of the text.
"""

from enum import Enum

import pytest
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.csi.inference import (
    Granularity,
    TextScore,
)
from pharia_skill.testing.dev.csi import DevCsi


class Input(BaseModel):
    question: str
    text: str


NORMALIZED_SCORE_HIGHLY_RELEVANT = 0.55
NORMALIZED_SCORE_RELEVANT = 0.1


class TextRelevancy(str, Enum):
    HIGHLY_RELEVANT = "highly_relevant"  # normalized score >= 0.55
    RELEVANT = "relevant"  # normalized score >= 0.1
    OTHER = "other"

    @classmethod
    def from_score(cls, score: float) -> "TextRelevancy":
        if score >= NORMALIZED_SCORE_HIGHLY_RELEVANT:
            return cls.HIGHLY_RELEVANT
        if score >= NORMALIZED_SCORE_RELEVANT:
            return cls.RELEVANT
        return cls.OTHER


class Explanation(BaseModel):
    start: int
    length: int
    relevancy: TextRelevancy


class Output(BaseModel):
    answer: str
    explanations: list[Explanation]


def filter_and_clamp(start: int, end: int, scores: list[TextScore]) -> list[TextScore]:
    """Filter and clamp the text scores for the specified range.

    The text scores that do not overlap with the specified range are filtered out.
    The ranges of the remaining text scores are clamped and offset to the specified range.
    """
    return [
        TextScore(
            start=max(score.start, start) - start,
            length=min(score.start + score.length, end) - max(score.start, start),
            score=score.score,
        )
        for score in scores
        if score.start < end and score.start + score.length > start
    ]


@skill
def highlighting(csi: Csi, input: Input) -> Output:
    first_prompt = f"Question: {input.question}\nText: "
    second_prompt = f"{input.text}\nAnswer:"
    prompt = first_prompt + second_prompt
    model = "pharia-1-llm-7b-control"
    params = CompletionParams(max_tokens=64, return_special_tokens=False)
    completion = csi.complete(model, prompt, params)
    answer = completion.text

    explanations = csi._explain(
        prompt=prompt,
        target=answer,
        model=model,
        granularity=Granularity.SENTENCE,
    )
    filtered_and_clamped_explanations = filter_and_clamp(
        len(first_prompt), len(first_prompt) + len(input.text), explanations
    )
    relevant_explanations = [
        Explanation(
            start=explanation.start,
            length=explanation.length,
            relevancy=TextRelevancy.from_score(explanation.score),
        )
        for explanation in filtered_and_clamped_explanations
        if explanation.score > 0
    ]

    return Output(answer=answer, explanations=relevant_explanations)


def test_filter_and_clamp():
    # 0 1 2 | 3 4 5 6 | 7 8 9
    start = 3
    end = 7
    before_range = TextScore(start=0, length=1, score=0.1)
    start_before_and_end_within_range = TextScore(start=2, length=4, score=0.2)
    start_before_and_end_on_range = TextScore(start=2, length=5, score=0.3)
    on_start = TextScore(start=3, length=1, score=0.4)
    start_on_and_end_on_range = TextScore(start=3, length=4, score=0.5)
    start_on_and_end_after_range = TextScore(start=3, length=6, score=0.6)
    start_within_and_end_after_range = TextScore(start=5, length=4, score=0.7)
    on_end = TextScore(start=6, length=1, score=0.8)
    after_range = TextScore(start=8, length=2, score=0.9)
    scores = [
        before_range,
        start_before_and_end_within_range,
        start_before_and_end_on_range,
        on_start,
        start_on_and_end_on_range,
        start_on_and_end_after_range,
        start_within_and_end_after_range,
        on_end,
        after_range,
    ]
    processed_scores = filter_and_clamp(start, end, scores)
    assert processed_scores == [
        TextScore(start=0, length=3, score=0.2),
        TextScore(start=0, length=4, score=0.3),
        TextScore(start=0, length=1, score=0.4),
        TextScore(start=0, length=4, score=0.5),
        TextScore(start=0, length=4, score=0.6),
        TextScore(start=2, length=2, score=0.7),
        TextScore(start=3, length=1, score=0.8),
    ]


@pytest.mark.kernel
def test_run_text_highlighting_skill():
    input_text = """Scientists at the European Southern Observatory announced a groundbreaking discovery today: microbial life detected in the water-rich atmosphere of Proxima Centauri b, our closest neighboring exoplanet.
The evidence, drawn from a unique spectral signature of organic compounds, hints at an ecosystem adapted to extreme conditions.
This finding, while not complex extraterrestrial life, significantly raises the prospects of life's commonality in the universe.
The international community is abuzz with plans for more focused research and potential interstellar missions."""
    input = Input(
        question="What is the ecosystem adapted to?",
        text=input_text,
    )
    csi = DevCsi()
    output = highlighting(csi, input)

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"

    highlighted_reference = ""
    previous_position = 0
    for explanation in output.explanations:
        highlighted_reference += input_text[previous_position : explanation.start]
        highlighted_reference += (
            BOLD + BLUE
            if explanation.relevancy == TextRelevancy.HIGHLY_RELEVANT
            else CYAN
        )
        highlighted_reference += input_text[
            explanation.start : explanation.start + explanation.length
        ]
        highlighted_reference += ENDC
        previous_position = explanation.start + explanation.length
    highlighted_reference = highlighted_reference.replace("\n", " ")
    print(
        """
Answer:
    {answer}

Reference:
    {highlighted_reference}

Legend:
    {bold}{blue}Highly relevant{endc}
    {cyan}Relevant{endc}""".format(
            answer=output.answer,
            highlighted_reference=highlighted_reference,
            bold=BOLD,
            blue=BLUE,
            cyan=CYAN,
            endc=ENDC,
        )
    )

    assert any(
        [
            "extreme conditions"
            in input_text[explanation.start : explanation.start + explanation.length]
            for explanation in output.explanations
            if explanation.relevancy is TextRelevancy.HIGHLY_RELEVANT
        ]
    )
