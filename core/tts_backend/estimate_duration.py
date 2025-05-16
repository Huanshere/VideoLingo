from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Dict, List, Pattern

import syllables
from g2p_en import G2p
from pypinyin import Style, pinyin

__all__ = ["SyllableEstimator", "Result"]

# ----------------------------------------------------------------------------
# Configuration containers
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class LangConfig:
    """Describes how to detect a language segment and count its syllables."""
    pattern: Pattern[str]
    joiner: str
    syllable_fn: Callable[[str], int]
    sec_per_syllable: float
    count_space: bool = True  # 默认为True，可以在语言配置中覆盖


@dataclass
class Result:
    """Outcome of ``SyllableEstimator.estimate``."""
    language_breakdown: Dict[str, int]
    total_syllables: int
    estimated_seconds: float
    punctuation: List[str]
    spaces: List[str]

    def __str__(self) -> str:  # pragma: no cover
        langs = ", ".join(f"{k}:{v}" for k, v in self.language_breakdown.items())
        return (
            f"<Result syllables={self.total_syllables} seconds={self.estimated_seconds:.2f} "
            f"langs=[{langs}]>"
        )


# ----------------------------------------------------------------------------
# Core estimator
# ----------------------------------------------------------------------------

class SyllableEstimator:
    """Multi‑lingual syllable counter with a lightweight duration model."""

    _g2p_en = G2p()

    def __init__(self) -> None:
        # Per‑language specifications ------------------------------------------------
        self.cfg: Dict[str, LangConfig] = {
            "en": LangConfig(
                pattern=re.compile(r"[a-zA-Z]+"),
                joiner=" ",
                syllable_fn=self._syllables_en,
                sec_per_syllable=0.225,
                count_space=False,  # 英文空格不计入停顿
            ),
            "zh": LangConfig(
                pattern=re.compile(r"[\u4e00-\u9fff]"),
                joiner="",
                syllable_fn=self._syllables_zh,
                sec_per_syllable=0.21,
                count_space=True,  # 中文空格计入停顿
            ),
            "ja": LangConfig(
                pattern=re.compile(r"[\u3040-\u309f\u30a0-\u30ff]"),
                joiner="",
                syllable_fn=self._syllables_ja,
                sec_per_syllable=0.21,
                count_space=True,  # 日文空格计入停顿
            ),
            "fr": LangConfig(
                pattern=re.compile(r"[a-zA-Zàâçéèêëîïôùûüÿœæ]+"),
                joiner=" ",
                syllable_fn=self._syllables_fr,
                sec_per_syllable=0.22,
                count_space=False,  # 法文空格不计入停顿
            ),
            "es": LangConfig(
                pattern=re.compile(r"[a-zA-Záéíóúüñ¿¡]+"),
                joiner=" ",
                syllable_fn=self._syllables_es,
                sec_per_syllable=0.22,
                count_space=False,  # 西班牙文空格不计入停顿
            ),
            "ko": LangConfig(
                pattern=re.compile(r"[\uac00-\ud7af\u1100-\u11ff]"),
                joiner=" ",
                syllable_fn=self._syllables_ko,
                sec_per_syllable=0.21,
                count_space=False,  # 韩文空格不计入停顿
            ),
        }

        # Punctuation handling -------------------------------------------------------
        self._punct_space = re.compile(r"\s+")
        self._punct_mid = re.compile(r"[，；：,;、]+")
        self._punct_end = re.compile(r"[。！？.!?]+")
        self._pause_seconds = {"space": 0.15, "punct": 0.10}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def estimate(self, text: str) -> Result:
        """Analyse *text*, which may contain multiple languages, and return ``Result``."""
        if not text or not text.strip():
            return Result({}, 0, 0.0, [], [])

        segments: List[str] = re.split(
            f"({self._punct_space.pattern}|{self._punct_mid.pattern}|{self._punct_end.pattern})",
            text,
        )

        breakdown: Dict[str, int] = {}
        puncts: List[str] = []
        spaces: List[str] = []
        total_syllables = 0
        total_seconds = 0.0

        for i, seg in enumerate(segments):
            if not seg:
                continue

            # Handle pauses -----------------------------------------------------
            if self._punct_space.fullmatch(seg):
                spaces.append(seg)
                left = segments[i-1] if i > 0 else ''
                right = segments[i+1] if i+1 < len(segments) else ''
                left_lang = self._detect(left)
                right_lang = self._detect(right)
                
                if (left and right and (self.cfg[left_lang].count_space or 
                                       self.cfg[right_lang].count_space)):
                    total_seconds += self._pause_seconds["space"]
                continue
            if self._punct_mid.fullmatch(seg) or self._punct_end.fullmatch(seg):
                puncts.append(seg)
                total_seconds += self._pause_seconds["punct"]
                continue

            # Language segment --------------------------------------------------
            lang = self._detect(seg)
            lang_cfg = self.cfg[lang]
            sylls = lang_cfg.syllable_fn(seg)
            breakdown[lang] = breakdown.get(lang, 0) + sylls
            total_syllables += sylls
            total_seconds += sylls * lang_cfg.sec_per_syllable

        return Result(breakdown, total_syllables, total_seconds, puncts, spaces)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _detect(self, text: str) -> str:
        """Return the first matching language code; default to 'en'."""
        for code, cfg in self.cfg.items():
            if cfg.pattern.search(text):
                return code
        return "en"

    # ---------------------------------------------------------------------
    # Language‑specific syllable counters (cached)
    # ---------------------------------------------------------------------

    @staticmethod
    @lru_cache(maxsize=8192)
    def _syllables_zh(text: str) -> int:
        cleaned = re.sub(r"[^\u4e00-\u9fff]", "", text)
        return len(pinyin(cleaned, style=Style.NORMAL))

    @staticmethod
    @lru_cache(maxsize=8192)
    def _syllables_ja(text: str) -> int:
        text = re.sub(r"[きぎしじちぢにひびぴみり][ょゅゃ]", "X", text)
        text = re.sub(r"[っー]", "", text)
        return len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", text))

    @staticmethod
    @lru_cache(maxsize=8192)
    def _syllables_fr(text: str) -> int:
        vowels = "aeiouyàâéèêëîïôùûüÿœæ"
        text = re.sub(r"e\b", "", text.lower())
        return max(1, len(re.findall(f"[{vowels}]+", text)))

    @staticmethod
    @lru_cache(maxsize=8192)
    def _syllables_es(text: str) -> int:
        vowels = "aeiouáéíóúü"
        return max(1, len(re.findall(f"[{vowels}]+", text.lower())))

    @staticmethod
    @lru_cache(maxsize=8192)
    def _syllables_ko(text: str) -> int:
        return len(re.findall(r"[\uac00-\ud7af]", text))

    # English relies on external libraries, so we keep access to ``self``

    @lru_cache(maxsize=8192)
    def _syllables_en(self, word: str) -> int:
        try:
            return syllables.estimate(word)
        except Exception:
            phones = self._g2p_en(word)
            return max(1, len([p for p in phones if any(v in p for v in "aeiou")]))


# ----------------------------------------------------------------------------
# Quick‑and‑dirty CLI for manual testing
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    # ------------
    # Test cases for manual testing
    # ------------
    test_cases = [
        "Hello world this is a test",  # pure English
        "你好世界 这是一个测试",      # Chinese with spaces
        "Hello 你好 world 世界",      # mixed English and Chinese
        "The weather is nice 所以我们去公园",  # mixed English and Chinese with spaces
        "我们需要在输出中体现空格的停顿时间",
        "I couldn't help but notice the vibrant colors of the autumn leaves cascading gently from the trees"
        "가을 나뭇잎이 부드럽게 떨어지는 생생한 색깔을 주목하지 않을 수 없었다"
    ]
    est = SyllableEstimator()
    for idx, sample in enumerate(test_cases, 1):
        print(f"\nTest case {idx}: {sample}")
        res = est.estimate(sample)
        print(res)
