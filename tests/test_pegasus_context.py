"""Tests for the opt-in TwelveLabs Pegasus visual-context integration.

Run from the repo root: `pytest tests/test_pegasus_context.py`

The live test is skipped unless TWELVELABS_API_KEY is set; the rest are
pure no-network unit tests that verify the feature is genuinely opt-in and
never breaks the pipeline.
"""
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import prompts
from core.utils import pegasus_context


def test_disabled_returns_empty(monkeypatch):
    """When the feature is off, get_visual_context() is a no-op."""
    monkeypatch.setattr(pegasus_context, "_is_enabled", lambda: False)
    assert pegasus_context.get_visual_context("does_not_matter.mp4") == ""


def test_enabled_without_key_returns_empty(monkeypatch):
    """Enabled but no key configured -> still a no-op (no crash, no call)."""
    monkeypatch.setattr(pegasus_context, "_is_enabled", lambda: True)
    monkeypatch.setattr(pegasus_context, "_get_api_key", lambda: "")
    assert pegasus_context.get_visual_context("does_not_matter.mp4") == ""


def test_summary_prompt_unchanged_without_context():
    """No visual context -> prompt has no visual section (backward compatible)."""
    prompt = prompts.get_summary_prompt("hello world", None, None)
    assert "On-screen Visual Context" not in prompt


def test_summary_prompt_injects_context():
    """Visual context is injected into the summary prompt when provided."""
    marker = "A red TESLA logo and the caption 'Model Y'."
    prompt = prompts.get_summary_prompt("hello world", None, marker)
    assert "On-screen Visual Context" in prompt
    assert marker in prompt


@pytest.mark.skipif(
    not os.getenv("TWELVELABS_API_KEY") or shutil.which("ffmpeg") is None,
    reason="requires TWELVELABS_API_KEY and ffmpeg for a live Pegasus call",
)
def test_live_pegasus_analyze(tmp_path):
    """Live contract check: asset upload + Pegasus analyze returns text.

    Mirrors the exact path the integration uses (direct asset upload then
    sync analyze with VideoContext_AssetId).
    """
    import subprocess

    from twelvelabs import TwelveLabs, VideoContext_AssetId

    clip = tmp_path / "clip.mp4"
    # 6s, 640x360 (>= 4s, >= 360p required by Pegasus).
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=6:size=640x360:rate=15",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(clip),
        ],
        check=True, capture_output=True,
    )

    client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])
    with open(clip, "rb") as f:
        asset = client.assets.create(method="direct", file=f, filename="clip.mp4")
    result = client.analyze(
        model_name="pegasus1.5",
        video=VideoContext_AssetId(asset_id=asset.id),
        prompt="Describe the on-screen content in one sentence.",
        max_tokens=512,
    )
    assert isinstance(result.data, str) and result.data.strip()
