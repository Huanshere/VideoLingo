"""Downstream language handling: joiners, code-switched joining and spaCy fallbacks (offline)."""
import shutil
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from core.asr_backend.qwen_asr_local import ISO_TO_QWEN
from core.spacy_utils import load_nlp_model as nlp_loader
from core.utils import config_utils
from core.utils.config_utils import get_joiner

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------
# get_joiner: every language auto detection can return has a joiner
# ------------------------------------------------------------------

@pytest.mark.parametrize("language", sorted(ISO_TO_QWEN))
def test_every_qwen_language_has_a_joiner(language):
    assert get_joiner(language) in ("", " ")


@pytest.mark.parametrize("language,joiner", [
    ("en", " "), ("zh", ""), ("ja", ""),                    # config.yaml lists
    ("ko", " "), ("vi", " "), ("pt", " "), ("ar", " "),     # built-in: spaced scripts
    ("th", ""), ("yue", ""), ("lo", ""), ("ZH", ""),        # built-in: unspaced scripts
])
def test_joiner_values(language, joiner):
    assert get_joiner(language) == joiner


def test_config_lists_override_built_in_rule():
    lists = {"language_split_with_space": ["th"], "language_split_without_space": ["ko"]}
    with patch.object(config_utils, "load_key_or", lambda key, default: lists.get(key, default)):
        assert get_joiner("th") == " " and get_joiner("ko") == ""


@pytest.mark.parametrize("language", [None, "", "auto"])
def test_unknown_language_still_raises(language):
    with pytest.raises(ValueError, match="Unsupported language code"):
        get_joiner(language)


# ------------------------------------------------------------------
# spaCy pipeline selection
# ------------------------------------------------------------------

def test_spacy_model_selection():
    assert nlp_loader.get_spacy_model("en") == "en_core_web_md"
    assert nlp_loader.get_spacy_model("ko") == "ko_core_news_md"
    assert nlp_loader.get_spacy_model("yue") == "zh_core_web_md"
    for language in ("ar", "th", "vi", "id", "tr", "hi", "fa"):
        assert nlp_loader.get_spacy_model(language) is None
    # Every Qwen language gets either a pipeline or the punctuation fallback, never the English model by accident.
    for language in ISO_TO_QWEN:
        model = nlp_loader.get_spacy_model(language)
        assert model is None or model.startswith(language if language != "yue" else "zh")


def _source(language):
    return patch.object(nlp_loader, "get_source_language", return_value=language)


def test_language_without_pipeline_uses_punctuation_splitting():
    with _source("ar"), patch.object(nlp_loader.spacy, "load", side_effect=AssertionError("no model")):
        nlp = nlp_loader.init_nlp()
    doc = nlp("مرحبا بكم. كيف حالكم؟ نحن بخير!")
    assert doc.has_annotation("SENT_START") and len(list(doc.sents)) == 3


def test_default_pipeline_download_failure_falls_back(monkeypatch):
    def fail(model):
        raise SystemExit(1)  # what spacy.cli.download does when it cannot fetch the package
    with _source("ko"), patch.object(nlp_loader.spacy, "load", side_effect=OSError("missing")), \
            patch.object(nlp_loader, "download", side_effect=fail):
        nlp = nlp_loader.init_nlp()
    assert nlp.lang == "xx" and "sentencizer" in nlp.pipe_names


def test_configured_pipeline_download_failure_still_fails():
    # A model the user configured (or the stock ones: en, zh, ja, ...) must not silently degrade.
    with _source("en"), patch.object(nlp_loader.spacy, "load", side_effect=OSError("missing")), \
            patch.object(nlp_loader, "download", side_effect=RuntimeError("offline")):
        with pytest.raises(RuntimeError, match="offline"):
            nlp_loader.init_nlp()


# ------------------------------------------------------------------
# The whole spaCy split stage runs for newly supported languages
# ------------------------------------------------------------------

@pytest.fixture
def project(tmp_path, monkeypatch):
    """A working directory with config.yaml (auto -> detected language) and cleaned_chunks.xlsx."""
    def make(language, words):
        text = (ROOT / "config.yaml").read_text(encoding="utf-8")
        text = text.replace("  language: 'en'\n  detected_language: 'en'",
                            f"  language: 'auto'\n  detected_language: '{language}'", 1)
        assert f"detected_language: '{language}'" in text
        (tmp_path / "config.yaml").write_text(text, encoding="utf-8")
        (tmp_path / "output/log").mkdir(parents=True)
        pd.DataFrame({"text": words}).to_excel(tmp_path / "output/log/cleaned_chunks.xlsx", index=False)
        monkeypatch.chdir(tmp_path)
        return tmp_path
    return make


def run_split_stage(nlp):
    from core.spacy_utils.split_by_mark import split_by_mark
    from core.spacy_utils.split_by_comma import split_by_comma_main
    from core.spacy_utils.split_by_connector import split_sentences_main
    from core.spacy_utils.split_long_by_root import split_long_by_root_main
    from core.utils.models import _3_1_SPLIT_BY_NLP
    split_by_mark(nlp)
    split_by_comma_main(nlp)
    split_sentences_main(nlp)
    split_long_by_root_main(nlp)
    return Path(_3_1_SPLIT_BY_NLP).read_text(encoding="utf-8").splitlines()


KO_WORDS = "안녕하세요. 저는 오늘 인생을 다시 시작한 이야기를 하려고 합니다. 여러분, 끈기가 중요합니다! 감사합니다.".split()


def test_korean_split_stage_runs_without_a_downloaded_model(project):
    # Mini: auto detected 'ko' and get_joiner raised "Unsupported language code: ko".
    project("ko", KO_WORDS)
    assert config_utils.get_source_language() == "ko"
    lines = run_split_stage(nlp_loader.punctuation_nlp())
    assert lines == ["안녕하세요.", "저는 오늘 인생을 다시 시작한 이야기를 하려고 합니다.",
                     "여러분, 끈기가 중요합니다!", "감사합니다."]


def test_thai_uses_unspaced_joiner_in_split_stage(project):
    project("th", ["สวัสดี", "ครับ", "วันนี้", "อากาศ", "ดี"])
    assert run_split_stage(nlp_loader.punctuation_nlp()) == ["สวัสดีครับวันนี้อากาศดี"]
