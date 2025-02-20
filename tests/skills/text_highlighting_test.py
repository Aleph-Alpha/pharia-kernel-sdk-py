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
    texts: list[str]


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


class ExplanationChunk(BaseModel):
    start: int
    length: int
    relevancy: TextRelevancy


class Explanation(BaseModel):
    chunks: list[ExplanationChunk]


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


def normalize(chunks: list[list[TextScore]]) -> list[list[TextScore]]:
    max_score = max(score.score for chunk in chunks for score in chunk)
    divider = max(1, max_score)
    return [
        [
            TextScore(
                start=score.start,
                length=score.length,
                score=max(score.score / divider, 0),
            )
            for score in chunk
        ]
        for chunk in chunks
    ]


@skill
def highlighting(csi: Csi, input: Input) -> Output:
    opening_prompt = f"Question: {input.question}\n"
    input_prompt_prefix = "Text: "
    input_prompt_suffix = "\n"
    input_prompts = "".join(
        [input_prompt_prefix + text + input_prompt_suffix for text in input.texts]
    )
    closing_prompt = "Answer:"
    prompt = opening_prompt + input_prompts + closing_prompt
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

    relevant_chunks = []
    source_start = len(opening_prompt)
    for text in input.texts:
        source_start += len(input_prompt_prefix)
        filtered_and_clamped_explanations = filter_and_clamp(
            source_start, source_start + len(text), explanations
        )
        source_start += len(text) + len(input_prompt_suffix)
        relevant_chunks.append(filtered_and_clamped_explanations)

    normalized_explanations = normalize(relevant_chunks)
    relevant_explanations = [
        Explanation(
            chunks=[
                ExplanationChunk(
                    start=explanation.start,
                    length=explanation.length,
                    relevancy=TextRelevancy.from_score(explanation.score),
                )
                for explanation in sublist
                if explanation.score > 0
            ]
        )
        for sublist in normalized_explanations
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


def test_normalize():
    score_1 = TextScore(start=1, length=1, score=-1)
    score_2 = TextScore(start=2, length=2, score=0)
    score_3 = TextScore(start=3, length=3, score=1)
    score_4 = TextScore(start=4, length=4, score=2)
    score_5 = TextScore(start=5, length=5, score=3)

    scores = [
        [
            score_1,
            score_2,
            score_3,
        ],
        [score_4, score_5],
    ]
    normalized_scores = normalize(scores)

    assert normalized_scores == [
        [
            TextScore(start=1, length=1, score=0),
            TextScore(start=2, length=2, score=0),
            TextScore(start=3, length=3, score=1 / 3),
        ],
        [
            TextScore(start=4, length=4, score=2 / 3),
            TextScore(start=5, length=5, score=3 / 3),
        ],
    ]


@pytest.mark.kernel
def test_run_text_highlighting_skill():
    input_text = """Scientists at the European Southern Observatory announced a groundbreaking discovery today: microbial life detected in the water-rich atmosphere of Proxima Centauri b, our closest neighboring exoplanet.
The evidence, drawn from a unique spectral signature of organic compounds, hints at an ecosystem adapted to extreme conditions.
This finding, while not complex extraterrestrial life, significantly raises the prospects of life's commonality in the universe.
The international community is abuzz with plans for more focused research and potential interstellar missions."""
    input_text2 = """Life on Earth is quite ubiquitous across the planet and has adapted over time to almost all the available environments in it, extremophiles and the deep biosphere thrive at even the most hostile ones. As a result, it is inferred that life in other celestial bodies may be equally adaptive. However, the origin of life is unrelated to its ease of adaptation and may have stricter requirements. A celestial body may not have any life on it, even if it were habitable."""
    input = Input(
        question="What is the ecosystem adapted to?",
        texts=[input_text, input_text2],
    )
    csi = DevCsi()
    output = highlighting(csi, input)

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"

    highlighted_reference = ""
    previous_position = 0

    for i, explanation in enumerate(output.explanations):
        current_input_text = input.texts[i]
        for chunk in explanation.chunks:
            highlighted_reference += current_input_text[previous_position : chunk.start]
            highlighted_reference += (
                BOLD + BLUE
                if chunk.relevancy == TextRelevancy.HIGHLY_RELEVANT
                else (CYAN if chunk.relevancy == TextRelevancy.RELEVANT else "")
            )
            highlighted_reference += current_input_text[
                chunk.start : chunk.start + chunk.length
            ]
            highlighted_reference += (
                "" if chunk.relevancy == TextRelevancy.OTHER else ENDC
            )
            previous_position = chunk.start + chunk.length
        highlighted_reference += current_input_text[previous_position:]
        highlighted_reference += "\n"
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

    flatten_explanations = [
        item for sublist in output.explanations for item in sublist.chunks
    ]
    assert any(
        [
            "extreme conditions"
            in input_text[explanation.start : explanation.start + explanation.length]
            for explanation in flatten_explanations
            if explanation.relevancy is TextRelevancy.HIGHLY_RELEVANT
        ]
    )
