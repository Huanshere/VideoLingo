"""Local content-addressed ASR results, independent of the disposable output folder."""

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from importlib.metadata import version, PackageNotFoundError
from core.utils import check_cancel

CACHE_DIR = Path(".cache/asr")
SCHEMA = 1  # Bump when preprocessing, model options or result interpretation changes.


def cache_key(media_file, whisper, demucs):
    digest = hashlib.md5(usedforsecurity=False)
    with open(media_file, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            check_cancel()
            digest.update(block)
    packages = {}
    for name in ("whisperx", "faster-whisper", "demucs"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    # Deliberately exclude credentials, filenames and translation/TTS settings.
    identity = {
        "schema": SCHEMA, "media_md5": digest.hexdigest(), "packages": packages,
        "runtime": whisper["runtime"], "model": whisper["model"],
        "language": whisper["language"], "demucs": bool(demucs),
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def valid_result(result):
    if not isinstance(result, dict) or not isinstance(result.get("segments"), list):
        return False
    for segment in result["segments"]:
        if not isinstance(segment, dict):
            return False
        words = segment.get("words") or []
        if not isinstance(words, list):
            return False
        if not words and not isinstance(segment.get("text"), str):
            return False
        if any(not isinstance(word, dict) or not isinstance(word.get("word"), str) for word in words):
            return False
        for item in [segment, *words]:
            if not isinstance(item, dict):
                return False
            for field in ("start", "end"):
                value = item.get(field)
                if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                    return False
            if item.get("start") is not None and item.get("end") is not None and item["end"] < item["start"]:
                return False
    return True


def read_result(key, part):
    try:
        entry = json.loads((CACHE_DIR / key / f"{part}.json").read_text(encoding="utf-8"))
        if (entry.get("schema") == SCHEMA and entry.get("key") == key
                and isinstance(entry.get("language"), str) and entry["language"] != "auto"
                and entry["language"] and valid_result(entry.get("result"))):
            return entry
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return None


def write_result(key, part, result, language):
    if not valid_result(result) or not isinstance(language, str) or not language or language == "auto":
        return
    directory = CACHE_DIR / key
    temporary = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as file:
            temporary = Path(file.name)
            json.dump({"schema": SCHEMA, "key": key, "language": language, "result": result}, file, allow_nan=False)
        os.replace(temporary, directory / f"{part}.json")
    except (OSError, TypeError, ValueError):
        # A read-only/full cache must not discard a successful transcription.
        pass
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
