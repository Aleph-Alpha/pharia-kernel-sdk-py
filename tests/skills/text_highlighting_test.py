"""
Given a question and a fitting text found via Rag, we want to generate an answer and highlight the relevant part of the text.
"""

from enum import Enum

import pytest
from pydantic import BaseModel

from pharia_skill import Csi, skill
from pharia_skill.csi.inference import (
    Granularity,
    TextScore,
)
from pharia_skill.testing.dev.csi import DevCsi


class Input(BaseModel):
    model: str
    prompt: str
    raw_completion: str
    focus_ranges: list[tuple[int, int]]


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


class Highlight(BaseModel):
    start: int
    end: int
    relevancy: TextRelevancy


class Chunk(BaseModel):
    start: int
    end: int
    highlights: list[Highlight]


class Output(BaseModel):
    chunks: list[Chunk]


class AssociatedExplanations(BaseModel):
    """The list of text scores associated with the specified range."""

    start: int
    end: int
    explanations: list[TextScore]


def associate_explanations(
    start: int, end: int, explanations: list[TextScore]
) -> AssociatedExplanations:
    """Filter and clamp the text scores for the specified range.

    The text scores that do not overlap with the specified range are filtered out.
    The ranges of the remaining text scores are clamped and offset to the specified range.
    """
    relevant_explanations = [
        explanation
        for explanation in explanations
        if explanation.start < end and explanation.start + explanation.length > start
    ]
    clamped_explanations = [
        TextScore(
            start=max(explanation.start, start) - start,
            length=min(explanation.start + explanation.length, end)
            - max(explanation.start, start),
            score=explanation.score,
        )
        for explanation in relevant_explanations
    ]
    return AssociatedExplanations(
        start=start, end=end, explanations=clamped_explanations
    )


def normalize(
    chunks: list[AssociatedExplanations],
) -> list[AssociatedExplanations]:
    max_score = max(
        explanation.score for chunk in chunks for explanation in chunk.explanations
    )
    divider = max(1, max_score)
    return [
        AssociatedExplanations(
            start=chunk.start,
            end=chunk.end,
            explanations=[
                TextScore(
                    start=explanation.start,
                    length=explanation.length,
                    score=max(explanation.score / divider, 0),
                )
                for explanation in chunk.explanations
            ],
        )
        for chunk in chunks
    ]


@skill
def highlighting(csi: Csi, input: Input) -> Output:
    explanations = csi._explain(
        prompt=input.prompt,
        target=input.raw_completion,
        model=input.model,
        granularity=Granularity.SENTENCE,
    )

    associated_explanations = [
        associate_explanations(range[0], range[1], explanations)
        for range in input.focus_ranges
    ]

    normalized_explanations = normalize(associated_explanations)

    chunks = [
        Chunk(
            start=sublist.start,
            end=sublist.end,
            highlights=[
                Highlight(
                    start=explanation.start,
                    end=explanation.start + explanation.length,
                    relevancy=TextRelevancy.from_score(explanation.score),
                )
                for explanation in sublist.explanations
                if explanation.score > 0
            ],
        )
        for sublist in normalized_explanations
    ]

    return Output(chunks=chunks)


def test_associate_explanations():
    # Given a range: 0 1 2 | 3 4 5 6 | 7 8 9
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

    associated_explanations = associate_explanations(start, end, scores)

    assert associated_explanations == AssociatedExplanations(
        start=start,
        end=end,
        explanations=[
            TextScore(start=0, length=3, score=0.2),
            TextScore(start=0, length=4, score=0.3),
            TextScore(start=0, length=1, score=0.4),
            TextScore(start=0, length=4, score=0.5),
            TextScore(start=0, length=4, score=0.6),
            TextScore(start=2, length=2, score=0.7),
            TextScore(start=3, length=1, score=0.8),
        ],
    )


def test_normalize():
    score_1 = TextScore(start=1, length=1, score=-1)
    score_2 = TextScore(start=2, length=2, score=0)
    score_3 = TextScore(start=3, length=1, score=1)
    score_4 = TextScore(start=4, length=4, score=2)
    score_5 = TextScore(start=5, length=5, score=3)
    scores = [
        AssociatedExplanations(
            start=1,
            end=4,
            explanations=[
                score_1,
                score_2,
                score_3,
            ],
        ),
        AssociatedExplanations(
            start=4,
            end=10,
            explanations=[score_4, score_5],
        ),
    ]

    normalized_scores = normalize(scores)

    assert normalized_scores == [
        AssociatedExplanations(
            start=1,
            end=4,
            explanations=[
                TextScore(start=1, length=1, score=0),
                TextScore(start=2, length=2, score=0),
                TextScore(start=3, length=1, score=1 / 3),
            ],
        ),
        AssociatedExplanations(
            start=4,
            end=10,
            explanations=[
                TextScore(start=4, length=4, score=2 / 3),
                TextScore(start=5, length=5, score=3 / 3),
            ],
        ),
    ]


@pytest.mark.kernel
def test_run_text_highlighting_skill():
    prompt = """Question: What is the ecosystem adapted to?
Text:
    Scientists at the European Southern Observatory announced a groundbreaking discovery today: microbial life detected in the water-rich atmosphere of Proxima Centauri b, our closest neighboring exoplanet.
The evidence, drawn from a unique spectral signature of organic compounds, hints at an ecosystem adapted to extreme conditions.
This finding, while not complex extraterrestrial life, significantly raises the prospects of life's commonality in the universe.
The international community is abuzz with plans for more focused research and potential interstellar missions.
Text:
    Life on Earth is quite ubiquitous across the planet and has adapted over time to almost all the available environments in it, extremophiles and the deep biosphere thrive at even the most hostile ones. As a result, it is inferred that life in other celestial bodies may be equally adaptive. However, the origin of life is unrelated to its ease of adaptation and may have stricter requirements. A celestial body may not have any life on it, even if it were habitable.
Answer:
    """
    input = Input(
        prompt=prompt,
        raw_completion="The ecosystem is adapted to extreme conditions.",
        model="pharia-1-llm-7b-control",
        focus_ranges=[(54, 624), (635, 1100)],
    )
    csi = DevCsi()
    output = highlighting(csi, input)

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"

    highlighted_reference = ""
    for i, chunk in enumerate(output.chunks):
        highlighted_reference += f"    [{i}]:\n"
        chunk_text = input.prompt[chunk.start : chunk.end]
        previous_position = 0
        for highlight in chunk.highlights:
            highlighted_reference += chunk_text[previous_position : highlight.start]
            highlighted_reference += (
                BOLD + BLUE
                if highlight.relevancy == TextRelevancy.HIGHLY_RELEVANT
                else (CYAN if highlight.relevancy == TextRelevancy.RELEVANT else "")
            )
            highlighted_reference += chunk_text[highlight.start : highlight.end]
            if highlight.relevancy != TextRelevancy.OTHER:
                highlighted_reference += ENDC
            previous_position = highlight.end
        highlighted_reference += chunk_text[previous_position:]
        highlighted_reference += "\n"
    print(
        """
Answer:
    {answer}

References:
{highlighted_reference}

Legend:
    {bold}{blue}Highly relevant{endc}
    {cyan}Relevant{endc}""".format(
            answer=input.raw_completion,
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
            in prompt[chunk.start + highlight.start : chunk.start + highlight.end]
            for chunk in output.chunks
            for highlight in chunk.highlights
            if highlight.relevancy is TextRelevancy.HIGHLY_RELEVANT
        ]
    )
