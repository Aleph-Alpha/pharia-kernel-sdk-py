"""
Given a question and a fitting text found via Rag, we want to generate an answer and highlight the relevant part of the text.
"""

from enum import Enum

from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.csi.inference import (
    Granularity,
)
from pharia_skill.testing.dev.csi import DevCsi


class Input(BaseModel):
    question: str
    text: str


class TextRelevancy(str, Enum):
    HIGHLY_RELEVANT = "highly_relevant"  # text score >= 1
    RELEVANT = "relevant"  # text score > 0
    IRRELEVANT = "irrelevant"  # text score <= 0


class Explanation(BaseModel):
    start: int
    length: int
    relevancy: TextRelevancy


class Output(BaseModel):
    answer: str
    explanations: list[Explanation]


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
    relevant_explanations = [
        Explanation(
            start=explanation.start - len(first_prompt),
            length=explanation.length,
            relevancy=TextRelevancy.HIGHLY_RELEVANT
            if explanation.score >= 1
            else TextRelevancy.RELEVANT,
        )
        for explanation in explanations
        if explanation.score > 0
        and explanation.start >= len(first_prompt)
        and explanation.start + explanation.length
        <= len(first_prompt) + len(input.text)
    ]

    return Output(answer=answer, explanations=relevant_explanations)


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
