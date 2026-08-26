import os
import json
from rich import print as rprint
from core.utils import load_key

# ------------------------------------------------------------------
# TwelveLabs Pegasus visual context (opt-in)
# ------------------------------------------------------------------
# VideoLingo summarizes and translates from the *transcript* only, so it is
# blind to on-screen text, products, UI labels, charts and logos that the
# narration never names. This helper asks TwelveLabs Pegasus to describe that
# visual layer once, and the description is fed into the terminology / summary
# prompt to disambiguate segmentation and translation of on-screen content.
#
# Fully opt-in: when `pegasus.enabled` is false or no API key is configured,
# `get_visual_context()` returns "" and the pipeline behaves exactly as before.
# Free API key + generous free tier at https://twelvelabs.io
# ------------------------------------------------------------------

# Cache the description so re-runs / resumed tasks don't re-analyze the video.
_VISUAL_CONTEXT_FILE = "output/log/pegasus_visual_context.json"

# Pegasus needs the analyzed window >= 4s; sync analyze handles videos <= 1h.
_PEGASUS_MODEL = "pegasus1.5"

_DEFAULT_PROMPT = (
    "You are assisting a video translation pipeline that only has the audio "
    "transcript and is blind to the screen. In 3-5 sentences, describe the "
    "visual context that the transcript cannot capture: on-screen text, "
    "titles, captions and labels; product, brand, app or character names "
    "shown; UI elements, charts or diagrams; and the overall setting. "
    "Quote any on-screen text verbatim. This helps disambiguate ambiguous "
    "terms and proper nouns during translation."
)


def _get_api_key():
    """Read the Pegasus key from config, falling back to the env var.

    Never hardcode a key; the integration reads its own from the repo's
    config or the TWELVELABS_API_KEY environment variable.
    """
    try:
        key = load_key("pegasus.api_key")
    except KeyError:
        key = ""
    if not key or key in ("", "YOUR_TWELVELABS_API_KEY"):
        key = os.getenv("TWELVELABS_API_KEY", "")
    return key


def _is_enabled():
    try:
        return bool(load_key("pegasus.enabled"))
    except KeyError:
        return False


def get_visual_context(video_file):
    """Return a short visual-context description for `video_file`, or "".

    Returns "" (and leaves the pipeline unchanged) when the feature is
    disabled, no key is configured, or the SDK isn't installed. Errors are
    swallowed with a warning so a Pegasus hiccup never breaks translation.
    """
    if not _is_enabled():
        return ""

    api_key = _get_api_key()
    if not api_key:
        rprint("[yellow]⚠️ Pegasus enabled but no API key set; skipping visual context.[/yellow]")
        return ""

    # Reuse cached context across resumed / re-run steps.
    if os.path.exists(_VISUAL_CONTEXT_FILE):
        with open(_VISUAL_CONTEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("context", "")

    try:
        from twelvelabs import TwelveLabs, VideoContext_AssetId
    except ImportError:
        rprint("[yellow]⚠️ `twelvelabs` not installed (pip install twelvelabs); skipping visual context.[/yellow]")
        return ""

    try:
        prompt = load_key("pegasus.prompt") or _DEFAULT_PROMPT
    except KeyError:
        prompt = _DEFAULT_PROMPT

    # Local-file asset upload via method="direct" is capped at 200MB.
    size_mb = os.path.getsize(video_file) / (1024 * 1024)
    if size_mb > 200:
        rprint(f"[yellow]⚠️ Video is {size_mb:.0f}MB (> 200MB direct-upload cap); skipping Pegasus visual context.[/yellow]")
        return ""

    rprint("[cyan]👁️ Extracting on-screen visual context with TwelveLabs Pegasus ...[/cyan]")
    try:
        client = TwelveLabs(api_key=api_key)
        with open(video_file, "rb") as f:
            asset = client.assets.create(
                method="direct",
                file=f,
                filename=os.path.basename(video_file),
            )
        result = client.analyze(
            model_name=_PEGASUS_MODEL,
            video=VideoContext_AssetId(asset_id=asset.id),
            prompt=prompt,
            max_tokens=load_key("pegasus.max_tokens") or 1024,
        )
        context = (result.data or "").strip()
    except Exception as e:  # noqa: BLE001 - never let Pegasus break the pipeline
        rprint(f"[yellow]⚠️ Pegasus visual context failed ({e}); continuing without it.[/yellow]")
        return ""

    os.makedirs(os.path.dirname(_VISUAL_CONTEXT_FILE), exist_ok=True)
    with open(_VISUAL_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump({"context": context}, f, ensure_ascii=False, indent=4)
    rprint(f"[green]✓ Visual context captured ({len(context)} chars) → `{_VISUAL_CONTEXT_FILE}`[/green]")
    return context


if __name__ == "__main__":
    # Manual smoke test: requires pegasus.enabled + a key, and a real video.
    from core._1_ytdlp import find_video_files
    print(get_visual_context(find_video_files()))
