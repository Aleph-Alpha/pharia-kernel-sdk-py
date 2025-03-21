from pharia_skill.csi.inference import CompletionDelta

from ..csi import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    Distribution,
    ExplanationRequest,
    FinishReason,
    Granularity,
    Logprob,
    Logprobs,
    Message,
    Role,
    TextScore,
    TokenUsage,
    TopLogprobs,
)
from ..wit.imports import inference as wit


def chat_params_to_wit(chat_params: ChatParams) -> wit.ChatParams:
    return wit.ChatParams(
        max_tokens=chat_params.max_tokens,
        temperature=chat_params.temperature,
        top_p=chat_params.top_p,
        frequency_penalty=chat_params.frequency_penalty,
        presence_penalty=chat_params.presence_penalty,
        logprobs=logprobs_to_wit(chat_params.logprobs),
    )


def message_to_wit(message: Message) -> wit.Message:
    return wit.Message(role=message.role.value, content=message.content)


def chat_request_to_wit(chat_request: ChatRequest) -> wit.ChatRequest:
    return wit.ChatRequest(
        model=chat_request.model,
        messages=[message_to_wit(msg) for msg in chat_request.messages],
        params=chat_params_to_wit(chat_request.params),
    )


def logprob_from_wit(logprob: wit.Logprob) -> Logprob:
    return Logprob(token=logprob.token, logprob=logprob.logprob)


def distribution_from_wit(distribution: wit.Distribution) -> Distribution:
    return Distribution(
        sampled=logprob_from_wit(distribution.sampled),
        top=[logprob_from_wit(logprob) for logprob in distribution.top],
    )


def token_usage_from_wit(usage: wit.TokenUsage) -> TokenUsage:
    return TokenUsage(prompt=usage.prompt, completion=usage.completion)


def completion_delta_from_wit(delta: wit.CompletionDelta) -> CompletionDelta:
    return CompletionDelta(
        text=delta.text,
        logprobs=[
            distribution_from_wit(distribution) for distribution in delta.logprobs
        ],
    )


def completion_from_wit(completion: wit.Completion) -> Completion:
    return Completion(
        text=completion.text,
        finish_reason=finish_reason_from_wit(completion.finish_reason),
        logprobs=[
            distribution_from_wit(distribution) for distribution in completion.logprobs
        ],
        usage=token_usage_from_wit(completion.usage),
    )


def completion_params_to_wit(
    completion_params: CompletionParams,
) -> wit.CompletionParams:
    return wit.CompletionParams(
        max_tokens=completion_params.max_tokens,
        temperature=completion_params.temperature,
        top_k=completion_params.top_k,
        top_p=completion_params.top_p,
        stop=completion_params.stop,
        return_special_tokens=completion_params.return_special_tokens,
        frequency_penalty=completion_params.frequency_penalty,
        presence_penalty=completion_params.presence_penalty,
        logprobs=logprobs_to_wit(completion_params.logprobs),
    )


def logprobs_to_wit(logprobs: Logprobs) -> wit.Logprobs:
    match logprobs:
        case "no":
            return wit.Logprobs_No()
        case "sampled":
            return wit.Logprobs_Sampled()
        case TopLogprobs():
            return wit.Logprobs_Top(value=logprobs.top)


def completion_request_to_wit(
    completion_request: CompletionRequest,
) -> wit.CompletionRequest:
    return wit.CompletionRequest(
        model=completion_request.model,
        prompt=completion_request.prompt,
        params=completion_params_to_wit(completion_request.params),
    )


def finish_reason_from_wit(reason: wit.FinishReason) -> FinishReason:
    match reason:
        case wit.FinishReason.STOP:
            return FinishReason.STOP
        case wit.FinishReason.LENGTH:
            return FinishReason.LENGTH
        case wit.FinishReason.CONTENT_FILTER:
            return FinishReason.CONTENT_FILTER


def role_from_wit(role: str) -> Role:
    """Convert a wit role (str) to a SDK role (Role).

    While we represent roles in the wit world as strings (no strict typing allows
    for faster iteration), there is value in exposing strongly typed roles in the
    Python SDK. We assume that any unknown role would come with a LLM response
    (after all, the user can only input the variants of the enum), so we default
    to Assistant.
    """
    match role:
        case "user":
            return Role.User
        case "system":
            return Role.System
        case _:
            return Role.Assistant


def message_from_wit(msg: wit.Message) -> Message:
    return Message(role=role_from_wit(msg.role), content=msg.content)


def chat_response_from_wit(response: wit.ChatResponse) -> ChatResponse:
    return ChatResponse(
        message=message_from_wit(response.message),
        finish_reason=finish_reason_from_wit(response.finish_reason),
        logprobs=[
            distribution_from_wit(distribution) for distribution in response.logprobs
        ],
        usage=token_usage_from_wit(response.usage),
    )


def granularity_to_wit(granularity: Granularity) -> wit.Granularity:
    match granularity:
        case Granularity.AUTO:
            return wit.Granularity.AUTO
        case Granularity.SENTENCE:
            return wit.Granularity.SENTENCE
        case Granularity.WORD:
            return wit.Granularity.WORD
        case Granularity.PARAGRAPH:
            return wit.Granularity.PARAGRAPH


def explanation_request_to_wit(
    explanation_request: ExplanationRequest,
) -> wit.ExplanationRequest:
    return wit.ExplanationRequest(
        prompt=explanation_request.prompt,
        target=explanation_request.target,
        model=explanation_request.model,
        granularity=granularity_to_wit(explanation_request.granularity),
    )


def text_score_from_wit(score: wit.TextScore) -> TextScore:
    return TextScore(start=score.start, length=score.length, score=score.score)
