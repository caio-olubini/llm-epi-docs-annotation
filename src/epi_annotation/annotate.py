from dataclasses import dataclass

from epi_annotation.config import ModelCfg
from epi_annotation.models import build_client
from epi_annotation.schema import DocumentAnnotation


@dataclass
class AnnotateResult:
    annotation: DocumentAnnotation
    input_tokens: int | None
    output_tokens: int | None


def annotate(text: str, model_cfg: ModelCfg, system_prompt: str) -> AnnotateResult:
    client = build_client(model_cfg)

    extra_kwargs: dict = {}
    if model_cfg.max_tokens is not None:
        extra_kwargs["max_tokens"] = model_cfg.max_tokens

    response, completion = client.chat.completions.create_with_completion(
        model=model_cfg.model_id,
        response_model=DocumentAnnotation,
        max_retries=0,  # retries are managed by the runner via tenacity
        temperature=model_cfg.temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        **extra_kwargs,
    )

    input_tokens, output_tokens = _extract_token_usage(completion)

    return AnnotateResult(
        annotation=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _extract_token_usage(completion: object) -> tuple[int | None, int | None]:
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None, None

    # OpenAI and Anthropic both expose .input_tokens/.output_tokens or
    # .prompt_tokens/.completion_tokens depending on the provider SDK version.
    input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)

    return input_tokens, output_tokens
