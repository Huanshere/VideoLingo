"""UI copy looked up by translate() must exist. Proper nouns must not be looked up.

The provider dropdown used to call translate() on every provider name. Company and
product names are not UI copy, so zh-CN (and every other locale) printed
"Translation not found" for OpenLux, 302.ai, SiliconFlow and Microsoft Edge.
"""
import ast
import json
from pathlib import Path

import pytest

import translations.translations as translations
from core.pipeline import (
    INVALID_TERMINOLOGY,
    INVALID_TRANSLATION,
    REVIEW_TERMINOLOGY,
    REVIEW_TRANSLATION,
    get_steps,
)
from core.st_utils.tts_settings import PROVIDERS, TRANSLATED_PROVIDERS, provider_label
from translations.translations import DISPLAY_LANGUAGES

ROOT = Path(__file__).resolve().parents[1]
LOCALES = sorted(DISPLAY_LANGUAGES.values())

# Terminal warnings after a zh-CN run. edge_tts is the default method, so the
# closed selectbox formats "Microsoft Edge" again and that warning was repeated.
SCREENSHOT_KEYS = ("OpenLux", "302.ai", "SiliconFlow", "Microsoft Edge")

# t(...) calls whose argument is not a string literal. Each expression is covered below.
DYNAMIC_T_ARGS = {
    "st.py": {"runner.current_label", "runner.pause_message"},
    "core/st_utils/download_video_section.py": {"text"},
    "core/st_utils/tts_settings.py": {"name"},
}


def _catalog(language):
    path = ROOT / "translations" / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _use_locale(monkeypatch, language):
    monkeypatch.setattr(translations, "get_current_language", lambda default="en": language)
    monkeypatch.setattr(translations, "load_translations", _catalog)


def _warning_lines(capsys):
    return [
        line for line in capsys.readouterr().out.splitlines()
        if line.startswith("Warning: Translation not found")
    ]


def _python_sources():
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "site-packages", "tests"} for part in path.parts):
            continue
        yield path


def _expression(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return ast.dump(node)


def _t_calls():
    """Every translate() call written as t(...): literal keys, and dynamic arguments."""
    literals = []
    dynamic = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            if not isinstance(func, ast.Name) or func.id != "t":
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                literals.append(arg.value)
                continue
            dynamic.append((relative, _expression(arg), node.lineno))
    return literals, dynamic


def _strings_bound_to(path, name):
    """String constants assigned to `name` in one file, including `a if cond else b`."""
    found = set()

    def collect(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.add(node.value)
        elif isinstance(node, ast.IfExp):
            collect(node.body)
            collect(node.orelse)

    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        collect(node.value)
    return found


def _pipeline_labels():
    labels = {REVIEW_TERMINOLOGY, INVALID_TERMINOLOGY, REVIEW_TRANSLATION, INVALID_TRANSLATION}
    for stage in ("transcribe", "subtitles", "dubbing", "all"):
        for label, _step in get_steps(stage, dubbing=True):
            labels.add(label)
    return labels


def test_dynamic_translate_calls_stay_known():
    _literals, dynamic = _t_calls()
    unexpected = [
        f"{path}:{line} t({arg})"
        for path, arg, line in dynamic
        if arg not in DYNAMIC_T_ARGS.get(path, set())
    ]
    assert unexpected == []


def test_literal_ui_keys_exist_in_every_locale():
    literals, _dynamic = _t_calls()
    assert literals
    missing = {
        language: sorted(key for key in set(literals) if key not in _catalog(language))
        for language in LOCALES
    }
    assert missing == {language: [] for language in LOCALES}


def test_locale_files_have_the_same_keys():
    catalogs = {language: set(_catalog(language)) for language in LOCALES}
    english = catalogs["en"]
    assert {language: sorted(english - keys) for language, keys in catalogs.items()} == {
        language: [] for language in LOCALES
    }


def test_step_and_pause_messages_exist_in_every_locale():
    keys = _pipeline_labels() | _strings_bound_to(
        "core/st_utils/download_video_section.py", "text"
    )
    assert len(keys) >= 4
    missing = {
        language: sorted(key for key in keys if key not in _catalog(language))
        for language in LOCALES
    }
    assert missing == {language: [] for language in LOCALES}


def test_brand_names_are_not_passed_to_translate(monkeypatch):
    def reject(key):
        raise AssertionError(key)

    monkeypatch.setattr(translations, "translate", reject)
    for name in PROVIDERS:
        if name in TRANSLATED_PROVIDERS:
            continue
        assert provider_label(name) == name


@pytest.mark.parametrize("language", LOCALES)
def test_provider_dropdown_does_not_warn(language, monkeypatch, capsys):
    """Format the provider list the way the selectbox does, including the selected name."""
    _use_locale(monkeypatch, language)
    selected = "Microsoft Edge"
    labels = [provider_label(name) for name in PROVIDERS]
    labels.extend(provider_label(selected) for _extra in range(2))

    assert _warning_lines(capsys) == []
    for name, label in zip(PROVIDERS, labels):
        if name in TRANSLATED_PROVIDERS:
            assert label == _catalog(language)[name]
        else:
            assert label == name
    assert all(label == selected for label in labels[-2:])


@pytest.mark.parametrize("language", LOCALES)
def test_screenshot_brands_are_not_identity_entries(language, monkeypatch, capsys):
    """Adding key: key rows would hide the warning. These names stay out of the dictionaries."""
    _use_locale(monkeypatch, language)
    for key in SCREENSHOT_KEYS:
        assert translations.translate(key) == key
    assert _warning_lines(capsys) == [
        f"Warning: Translation not found for key '{key}' in language '{language}'"
        for key in SCREENSHOT_KEYS
    ]


def test_selectbox_formats_providers_without_warnings(monkeypatch, capsys):
    """The dubbing sidebar formats every provider, then the selected one again."""
    from streamlit.testing.v1 import AppTest
    from core.utils import config_utils

    _use_locale(monkeypatch, "zh-CN")
    monkeypatch.setattr(config_utils, "load_key", lambda key: "edge_tts" if key == "tts_method" else "")
    monkeypatch.setattr(config_utils, "load_key_or", lambda key, default: default)

    def page():
        from core.st_utils.tts_settings import PROVIDERS, select_tts_method
        select_tts_method({method: method for methods in PROVIDERS.values() for method in methods})

    app = AppTest.from_function(page, default_timeout=30).run()

    assert not app.exception
    assert [box.label for box in app.selectbox] == ["配音服务商"]
    assert _warning_lines(capsys) == []


def test_translated_provider_names_are_ui_copy():
    assert TRANSLATED_PROVIDERS <= set(PROVIDERS)
    for language in LOCALES:
        catalog = _catalog(language)
        missing = sorted(name for name in TRANSLATED_PROVIDERS if name not in catalog)
        assert missing == []
