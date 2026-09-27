"""Duration estimation must work on a fresh install without NLTK corpora."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_estimator_starts_when_optional_g2p_data_is_unavailable():
    code = """
import sys
import types

g2p = types.ModuleType('g2p_en')
class MissingData:
    def __init__(self):
        raise LookupError('NLTK cmudict is unavailable')
g2p.G2p = MissingData
sys.modules['g2p_en'] = g2p

from core.tts_backend.estimate_duration import init_estimator
estimator = init_estimator()
assert estimator.count_syllables('Hello world', 'en') > 0
assert estimator.count_syllables('你好世界', 'zh') == 4
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
