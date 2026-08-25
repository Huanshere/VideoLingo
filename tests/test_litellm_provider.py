import sys
import os
import json
import types
from unittest import mock
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_mock_response(content="test response"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    config = {
        "api": {
            "key": "test-key-123",
            "base_url": "https://api.example.com",
            "model": "anthropic/claude-haiku-4-5",
            "llm_support_json": False,
            "provider": "litellm",
        },
        "display_language": "en",
        "language_split_with_space": ["en"],
        "language_split_without_space": ["zh"],
    }
    config_file = tmp_path / "config.yaml"
    from ruamel.yaml import YAML

    yaml = YAML()
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    monkeypatch.setattr("core.utils.config_utils.CONFIG_PATH", str(config_file))
    return config_file


class TestCallLiteLLM:
    def test_basic_completion(self):
        mock_resp = _make_mock_response("hello world")
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            result = _call_litellm(
                "anthropic/claude-haiku-4-5",
                [{"role": "user", "content": "say hi"}],
                None,
                "",
                "test-key",
            )
            assert result.choices[0].message.content == "hello world"
            mock_comp.assert_called_once()
            call_kwargs = mock_comp.call_args[1]
            assert call_kwargs["model"] == "anthropic/claude-haiku-4-5"
            assert call_kwargs["drop_params"] is True
            assert call_kwargs["api_key"] == "test-key"

    def test_drop_params_always_true(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            _call_litellm("gemini/gemini-pro", [{"role": "user", "content": "test"}], None, "", "key")
            assert mock_comp.call_args[1]["drop_params"] is True

    def test_api_key_omitted_when_empty(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            _call_litellm("openai/gpt-4o", [{"role": "user", "content": "test"}], None, "", "")
            assert "api_key" not in mock_comp.call_args[1]

    def test_base_url_forwarded_when_set(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            _call_litellm(
                "openai/gpt-4o",
                [{"role": "user", "content": "test"}],
                None,
                "https://custom.endpoint.com",
                "key",
            )
            assert mock_comp.call_args[1]["api_base"] == "https://custom.endpoint.com"

    def test_base_url_omitted_when_empty(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            _call_litellm("anthropic/claude-haiku-4-5", [{"role": "user", "content": "test"}], None, "", "key")
            assert "api_base" not in mock_comp.call_args[1]

    def test_json_response_format_forwarded(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            rf = {"type": "json_object"}
            _call_litellm("openai/gpt-4o", [{"role": "user", "content": "test"}], rf, "", "key")
            assert mock_comp.call_args[1]["response_format"] == rf

    def test_response_format_omitted_when_none(self):
        mock_resp = _make_mock_response()
        with mock.patch("litellm.completion", return_value=mock_resp) as mock_comp:
            from core.utils.ask_gpt import _call_litellm

            _call_litellm("openai/gpt-4o", [{"role": "user", "content": "test"}], None, "", "key")
            assert "response_format" not in mock_comp.call_args[1]


class TestAskGptProviderRouting:
    def test_litellm_provider_routes_to_litellm(self, tmp_config):
        mock_resp = _make_mock_response('{"code": 200}')
        with mock.patch("core.utils.ask_gpt._call_litellm", return_value=mock_resp) as mock_lit, \
             mock.patch("core.utils.ask_gpt._call_openai") as mock_oai:
            from core.utils.ask_gpt import ask_gpt

            ask_gpt("test prompt", log_title="test_routing")
            mock_lit.assert_called_once()
            mock_oai.assert_not_called()

    def test_openai_provider_routes_to_openai(self, tmp_config):
        from core.utils.config_utils import update_key

        update_key("api.provider", "openai")
        mock_resp = _make_mock_response("ok")
        with mock.patch("core.utils.ask_gpt._call_openai", return_value=mock_resp) as mock_oai, \
             mock.patch("core.utils.ask_gpt._call_litellm") as mock_lit:
            from core.utils.ask_gpt import ask_gpt

            ask_gpt("test prompt", log_title="test_routing_oai")
            mock_oai.assert_called_once()
            mock_lit.assert_not_called()


class TestCallOpenAI:
    def test_ark_base_url_override(self):
        with mock.patch("core.utils.ask_gpt.OpenAI") as MockClient:
            mock_instance = mock.MagicMock()
            mock_instance.chat.completions.create.return_value = _make_mock_response()
            MockClient.return_value = mock_instance

            from core.utils.ask_gpt import _call_openai

            _call_openai("model", [{"role": "user", "content": "hi"}], None, "https://ark.example.com/api", "key")
            assert MockClient.call_args[1]["base_url"] == "https://ark.cn-beijing.volces.com/api/v3"

    def test_v1_appended_when_missing(self):
        with mock.patch("core.utils.ask_gpt.OpenAI") as MockClient:
            mock_instance = mock.MagicMock()
            mock_instance.chat.completions.create.return_value = _make_mock_response()
            MockClient.return_value = mock_instance

            from core.utils.ask_gpt import _call_openai

            _call_openai("model", [{"role": "user", "content": "hi"}], None, "https://api.example.com", "key")
            assert MockClient.call_args[1]["base_url"] == "https://api.example.com/v1"
