import json
import importlib
from types import SimpleNamespace

import pytest

from core.asr_backend.transcript_quality import find_repetition_loops
from core.utils.decorator import NonRetryableError, except_handler

ask_gpt_module = importlib.import_module('core.utils.ask_gpt')


def test_repetition_loop_detection():
    words = ['normal', 'speech'] + ['you', 'know'] * 12 + ['continues']
    loops = find_repetition_loops(words, min_cycles=12)
    assert len(loops) == 1
    assert loops[0]['pattern'] == ['you', 'know']
    assert loops[0]['cycles'] == 12


def test_normal_repetition_is_not_rejected():
    assert find_repetition_loops(['very', 'very', 'useful'], min_cycles=12) == []


def test_non_retryable_error_is_not_retried():
    calls = 0

    @except_handler('failed', retry=5, delay=0)
    def fail_once():
        nonlocal calls
        calls += 1
        raise NonRetryableError('limit reached')

    with pytest.raises(NonRetryableError):
        fail_once()
    assert calls == 1


def test_usage_is_recorded_by_stage(tmp_path, monkeypatch):
    usage_file = tmp_path / 'usage.json'
    monkeypatch.setattr(ask_gpt_module, 'USAGE_FILE', str(usage_file))
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120)
    totals = ask_gpt_module._record_usage(usage, 'translate_faithfulness')
    assert totals['total_tokens'] == 120
    assert totals['stages']['translate_faithfulness'] == {'requests': 1, 'total_tokens': 120}
    assert json.loads(usage_file.read_text())['requests'] == 1


def test_usage_limit_raises_non_retryable_error(tmp_path, monkeypatch):
    usage_file = tmp_path / 'usage.json'
    usage_file.write_text(json.dumps({'total_tokens': 1000}))
    monkeypatch.setattr(ask_gpt_module, 'USAGE_FILE', str(usage_file))
    monkeypatch.setattr(
        ask_gpt_module,
        '_load_optional_key',
        lambda key, default: 1000 if key == 'api.max_total_tokens' else default,
    )
    with pytest.raises(NonRetryableError, match='token limit reached'):
        ask_gpt_module._check_usage_limit()


def test_official_deepseek_thinking_parameter_is_configurable(monkeypatch):
    monkeypatch.setattr(
        ask_gpt_module,
        '_load_optional_key',
        lambda key, default: 'disabled' if key == 'api.thinking' else default,
    )
    assert ask_gpt_module._deepseek_extra_body('https://api.deepseek.com/v1') == {
        'thinking': {'type': 'disabled'}
    }
    assert ask_gpt_module._deepseek_extra_body('https://openrouter.ai/api/v1') is None
