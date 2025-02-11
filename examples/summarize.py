from enum import Enum
from typing import NamedTuple

from pydantic import BaseModel, RootModel

from pharia_skill import (
    ChunkParams,
    CompletionParams,
    CompletionRequest,
    Csi,
    Language,
    skill,
)

MODEL = "luminous-base-control"
# wrong model, prompts need to be updated
MODEL = "llama-3.1-8b-instruct"
MODEL_CONTEXT_SIZE = 2048


class SummaryLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class Input(BaseModel):
    text: str
    length: SummaryLength
    language: Language | None = None


class Output(RootModel[str]):
    root: str


# English and German prompts for different intended summary lengths.
SUMMARIZATION_PROMPTS = {
    SummaryLength.SHORT: {
        Language.English: "Create a concise summary of the following text. Summarize the most important points in 2-3 sentences so that the core content is clear. Avoid unnecessary details.",
        Language.German: "Erstelle eine prägnante Zusammenfassung des folgenden Textes. Fasse das Allerwichtigste in 2-3 Sätzen zusammen, sodass der Kerninhalt klar wird. Vermeide unnötige Details.",
    },
    SummaryLength.MEDIUM: {
        Language.English: "Create a summary of the following text. Summarize the main points and include details, similar to an abstract. Make sure that the summary is informative and precise.",
        Language.German: "Erstelle eine Zusammenfassung des folgenden Textes. Fasse die Hauptpunkte zusammen und integriere auch Details, ähnlich wie in einem Abstract. Achte darauf, dass die Zusammenfassung informativ und präzise ist.",
    },
    SummaryLength.LONG: {
        Language.English: "Create a comprehensive summary of the following text. Summarize all relevant information so that no details are missing. The summary should comprise several paragraphs and cover the entire content. Make sure that the summary is logically structured and easy to understand.",
        Language.German: "Erstelle eine umfassende Zusammenfassung des folgenden Textes. Fasse alle relevanten Informationen zusammen, sodass keine Details fehlen. Die Zusammenfassung soll mehrere Paragraphen umfassen und den gesamten Inhalt abdecken. Achte darauf, dass die Zusammenfassung logisch strukturiert und leicht verständlich ist.",
    },
}


class Instruction(NamedTuple):
    """An instruction, that can turn itself into a prompt string if given a chunk of text.

    Attributes:
        summarization_prompt (str, required): A summarization instruction for a concrete language and length.
    """

    summarization_prompt: str

    @staticmethod
    def for_length_and_language(length: SummaryLength, language: Language):
        return Instruction(SUMMARIZATION_PROMPTS[length][language])

    def request(self, text: str) -> CompletionRequest:
        params = CompletionParams(max_tokens=MODEL_CONTEXT_SIZE // 4)
        return CompletionRequest(model=MODEL, prompt=self.prompt(text), params=params)

    def prompt(self, text: str) -> str:
        return f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{self.summarization_prompt}

{text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"""


@skill
def summarize(csi: Csi, input: Input) -> Output:
    # extract the intended language of the answer out of the question
    language = (
        input.language
        or csi.select_language(input.text, [Language.English, Language.German])
        or Language.English
    )

    # get the correct instruction according to the intended length and language
    instruction = Instruction.for_length_and_language(input.length, language)
    params = ChunkParams(model=MODEL, max_tokens=(MODEL_CONTEXT_SIZE * 3) // 4 - 200)

    last_no_summaries = None
    text = input.text
    # iterate on the text to summarize
    while True:
        # we chunk the text to summarize
        requests = [instruction.request(chunk) for chunk in csi.chunk(text, params)]
        # and summarize each chunk
        summaries = [
            completion.text.strip() for completion in csi.complete_concurrent(requests)
        ]
        # resulting in a (hopefully) smaller text
        text = "\n".join(summaries)
        # if there has been just one chunk/summary, we are done
        if len(summaries) == 1:
            break
        # if we have not got fewer chunks in this round, give up
        if last_no_summaries and len(summaries) == last_no_summaries:
            break
        last_no_summaries = len(summaries)
    return Output(root=text)
