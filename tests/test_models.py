import os
import pytest
from unittest.mock import patch, MagicMock

from epi_annotation.config import ModelCfg


def make_model_cfg(provider="openai", model_id="gpt-4o", mode="tools_strict"):
    return ModelCfg(name="test", provider=provider, model_id=model_id, mode=mode)


def test_missing_openai_key_exits_with_provider_name_in_message(capsys):
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            from epi_annotation.models import build_client
            build_client(make_model_cfg(provider="openai"))

    captured = capsys.readouterr()
    assert "openai" in captured.err.lower()
    assert "OPENAI_API_KEY" in captured.err


def test_missing_anthropic_key_exits_with_provider_name_in_message(capsys):
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            from epi_annotation.models import build_client
            build_client(make_model_cfg(provider="anthropic", model_id="claude-sonnet-4-6"))

    captured = capsys.readouterr()
    assert "anthropic" in captured.err.lower()
    assert "ANTHROPIC_API_KEY" in captured.err


def test_missing_google_key_exits_with_provider_name_in_message(capsys):
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            from epi_annotation.models import build_client
            build_client(make_model_cfg(provider="google", model_id="gemini-1.5-pro"))

    captured = capsys.readouterr()
    assert "google" in captured.err.lower()
    assert "GOOGLE_API_KEY" in captured.err


def test_error_message_does_not_contain_key_value(capsys):
    """A leaked key in the error message would be a security issue."""
    secret = "sk-supersecret-key-value"
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        with pytest.raises(SystemExit):
            from epi_annotation.models import build_client
            build_client(make_model_cfg(provider="openai"))

    captured = capsys.readouterr()
    assert secret not in captured.err


def test_build_client_returns_instructor_client_when_key_is_set():
    import instructor
    mock_instructor = MagicMock(spec=instructor.Instructor)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}):
        with patch("openai.OpenAI") as mock_openai:
            with patch("instructor.from_openai", return_value=mock_instructor) as mock_from_openai:
                from epi_annotation.models import build_client
                result = build_client(make_model_cfg(provider="openai"))

    mock_openai.assert_called_once_with(api_key="sk-fake", base_url=None)
    mock_from_openai.assert_called_once_with(mock_openai.return_value, mode=instructor.Mode.TOOLS_STRICT)
    assert result is mock_instructor


def test_build_client_uses_explicit_mode_from_config():
    import instructor

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}):
        with patch("openai.OpenAI"):
            with patch("instructor.from_openai") as mock_from_openai:
                from epi_annotation.models import build_client
                build_client(make_model_cfg(provider="openai", mode="json_mode"))

    _, kwargs = mock_from_openai.call_args
    assert kwargs["mode"] == instructor.Mode.JSON


def test_build_client_exits_on_unknown_mode(capsys):
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}):
        with patch("openai.OpenAI"):
            with pytest.raises(SystemExit):
                from epi_annotation.models import build_client
                build_client(make_model_cfg(provider="openai", mode="not_a_real_mode"))

    assert "not_a_real_mode" in capsys.readouterr().err


def test_build_client_uses_anthropic_base_url():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant"}):
        with patch("openai.OpenAI") as mock_openai:
            with patch("instructor.from_openai"):
                from epi_annotation.models import build_client
                build_client(make_model_cfg(provider="anthropic", model_id="claude-sonnet-4-6"))

    _, kwargs = mock_openai.call_args
    assert kwargs["api_key"] == "sk-ant"
    assert kwargs["base_url"] == "https://api.anthropic.com/v1/"


def test_build_client_uses_google_base_url():
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "sk-goog"}):
        with patch("openai.OpenAI") as mock_openai:
            with patch("instructor.from_openai"):
                from epi_annotation.models import build_client
                build_client(make_model_cfg(provider="google", model_id="gemini-2.5-flash"))

    _, kwargs = mock_openai.call_args
    assert kwargs["api_key"] == "sk-goog"
    assert kwargs["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
