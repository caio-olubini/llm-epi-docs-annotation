import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from epi_annotation.annotate import AnnotateResult, annotate, _extract_token_usage
from epi_annotation.config import ModelCfg
from epi_annotation.schema import Disease, DocumentAnnotation, LocationLevel, EpiObservation


def make_model_cfg(max_tokens=None):
    return ModelCfg(name="test", provider="openai", model_id="gpt-4o", max_tokens=max_tokens)


def make_valid_annotation():
    return DocumentAnnotation(
        diseases_covered=[Disease.dengue],
        observations=[
            EpiObservation(
                disease=Disease.dengue,
                location_name="Brasil",
                location_level=LocationLevel.national,
            )
        ],
    )


def make_mock_client(annotation, usage=None):
    completion = SimpleNamespace(usage=usage)
    mock_client = MagicMock()
    mock_client.chat.completions.create_with_completion.return_value = (annotation, completion)
    return mock_client


def test_annotate_returns_valid_annotation_result():
    annotation = make_valid_annotation()
    mock_client = make_mock_client(annotation)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        result = annotate("bulletin text", make_model_cfg(), "system prompt")

    assert isinstance(result, AnnotateResult)
    assert result.annotation is annotation
    assert isinstance(result.annotation, DocumentAnnotation)


def test_annotate_passes_system_prompt_and_text_as_messages():
    annotation = make_valid_annotation()
    mock_client = make_mock_client(annotation)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        annotate("the bulletin", make_model_cfg(), "the system prompt")

    call_kwargs = mock_client.chat.completions.create_with_completion.call_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "the system prompt"}
    assert messages[1] == {"role": "user", "content": "the bulletin"}


def test_annotate_passes_model_id():
    annotation = make_valid_annotation()
    mock_client = make_mock_client(annotation)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        annotate("text", make_model_cfg(), "prompt")

    call_kwargs = mock_client.chat.completions.create_with_completion.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"


def test_annotate_passes_max_tokens_when_configured():
    annotation = make_valid_annotation()
    mock_client = make_mock_client(annotation)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        annotate("text", make_model_cfg(max_tokens=2048), "prompt")

    call_kwargs = mock_client.chat.completions.create_with_completion.call_args.kwargs
    assert call_kwargs["max_tokens"] == 2048


def test_annotate_omits_max_tokens_when_not_configured():
    annotation = make_valid_annotation()
    mock_client = make_mock_client(annotation)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        annotate("text", make_model_cfg(max_tokens=None), "prompt")

    call_kwargs = mock_client.chat.completions.create_with_completion.call_args.kwargs
    assert "max_tokens" not in call_kwargs


def test_extract_token_usage_reads_openai_style_fields():
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=50)
    completion = SimpleNamespace(usage=usage)
    input_tok, output_tok = _extract_token_usage(completion)
    assert input_tok == 100
    assert output_tok == 50


def test_extract_token_usage_reads_anthropic_style_fields():
    usage = SimpleNamespace(input_tokens=200, output_tokens=80)
    completion = SimpleNamespace(usage=usage)
    input_tok, output_tok = _extract_token_usage(completion)
    assert input_tok == 200
    assert output_tok == 80


def test_extract_token_usage_returns_none_when_usage_is_absent():
    completion = SimpleNamespace(usage=None)
    input_tok, output_tok = _extract_token_usage(completion)
    assert input_tok is None
    assert output_tok is None


def test_annotate_surfaces_token_usage_in_result():
    annotation = make_valid_annotation()
    usage = SimpleNamespace(input_tokens=300, output_tokens=60)
    mock_client = make_mock_client(annotation, usage=usage)

    with patch("epi_annotation.annotate.build_client", return_value=mock_client):
        result = annotate("text", make_model_cfg(), "prompt")

    assert result.input_tokens == 300
    assert result.output_tokens == 60
