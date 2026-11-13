"""The Chinese and Japanese faces of the subtitle typesetter, fetched on first use.

Each is 10 MB or more, too big for the repository. The variable Noto Sans
fonts of google/fonts are downloaded at a fixed commit, checked against their
SHA-256 and cut down to one static instance at weight 450 ("Book"): libass
draws a variable font at its default instance only, and the sizes in
typeset.py were chosen against this weight. scripts/build_subtitle_fonts.py
builds the same files from a google/fonts checkout. Without a network, the
variable font put in fonts/ by hand is used instead (`local_source`).
"""
import hashlib
import os
import tempfile
import time

import requests
from rich import print as rprint
from rich.markup import escape

from . import check_cancel
from .typeset import FONT_FILES, FONTS_DIR

GOOGLE_FONTS_COMMIT = "5bb28733cec313b63fbd415b574b5ae35c8aa8b8"
MIRRORS = (
    "https://github.com/google/fonts/raw/{commit}/ofl/{path}",
    "https://cdn.jsdelivr.net/gh/google/fonts@{commit}/ofl/{path}",
    "https://fastly.jsdelivr.net/gh/google/fonts@{commit}/ofl/{path}",
    "https://gcore.jsdelivr.net/gh/google/fonts@{commit}/ofl/{path}",
)
# Family the typesetter asks for -> (file in google/fonts/ofl, its SHA-256, upstream family)
DOWNLOADS = {
    "Noto Sans SC Book": (
        "notosanssc/NotoSansSC%5Bwght%5D.ttf",
        "a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da", "Noto Sans SC",
    ),
    "Noto Sans TC Book": (
        "notosanstc/NotoSansTC%5Bwght%5D.ttf",
        "864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f", "Noto Sans TC",
    ),
    "Noto Sans HK Book": (
        "notosanshk/NotoSansHK%5Bwght%5D.ttf",
        "76098ee78ec234cd4f8c950742b3f766fea2f8b43d5180d901048f4fc86c6849", "Noto Sans HK",
    ),
    "Noto Sans JP Book": (
        "notosansjp/NotoSansJP%5Bwght%5D.ttf",
        "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f", "Noto Sans JP",
    ),
}
MAX_BYTES = 40 * 1024 * 1024
MB = 1024 * 1024
# Seconds to get one file over all the mirrors, and to wait before trying a family again after that
DEADLINE = 600
RETRY_AFTER = 600
_FAILED = {}  # family -> time.monotonic() when its download failed
BOOK_WEIGHT = 450
REGULAR_ONLY = ~0b1100001, 0b1000000  # fsSelection: clear ITALIC, BOLD and REGULAR, then set REGULAR


def set_names(font, records, drop=(1, 2, 3, 4, 6, 16, 17, 21, 22, 25)):
    """Name the face anew: libass finds a face by its family (name ID 1) or full name (name ID 4)."""
    name = font["name"]
    for name_id in drop:
        name.removeNames(nameID=name_id)
    for name_id, value in records:
        name.setName(value, name_id, 3, 1, 0x409)
        name.setName(value, name_id, 1, 0, 0)
    os2 = font["OS/2"]
    os2.fsSelection = (os2.fsSelection & REGULAR_ONLY[0]) | REGULAR_ONLY[1]
    font["head"].macStyle = 0


def book(source, family, stem):
    """The static weight-450 instance of a variable Noto Sans CJK font, as family "<family> Book"."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    font = instancer.instantiateVariableFont(TTFont(source), {"wght": BOOK_WEIGHT}, inplace=False)
    set_names(
        font,
        (
            (1, f"{family} Book"), (2, "Regular"), (3, f"{stem}-Book;instance"), (4, f"{family} Book"),
            (6, f"{stem}-Book"), (16, family), (17, "Book"),
        ),
    )
    if "STAT" in font:
        del font["STAT"]
    font["OS/2"].usWeightClass = BOOK_WEIGHT
    return font


def font_path(family):
    return os.path.join(FONTS_DIR, FONT_FILES[family])


def missing(families):
    """The families of `families` that can be downloaded and are not there yet."""
    return [family for family in dict.fromkeys(families) if family in DOWNLOADS and not os.path.isfile(font_path(family))]


def local_names(family):
    """The names the variable font of `family` has on GitHub and in the zip of fonts.google.com."""
    stem = DOWNLOADS[family][2].replace(" ", "")
    return f"{stem}[wght].ttf", f"{stem}-VariableFont_wght.ttf"


def local_source(family):
    """The variable font of `family` that was put in fonts/ by hand, None when there is none (or it is not that font)."""
    upstream = DOWNLOADS[family][2]
    for name in local_names(family):
        path = os.path.join(FONTS_DIR, name)
        if not os.path.isfile(path):
            continue
        try:
            from fontTools.ttLib import TTFont

            font = TTFont(path, lazy=True)
            names = {font["name"].getDebugName(name_id) for name_id in (1, 16)}
            axes = {axis.axisTag for axis in font["fvar"].axes} if "fvar" in font else set()
            font.close()
        except Exception as error:
            rprint(f"[yellow]⚠️ Could not read {escape(path)}: {escape(str(error))}[/yellow]")
            continue
        if upstream in names and "wght" in axes:
            return path
        rprint(f"[yellow]⚠️ {escape(path)} is not the variable font of {upstream}, it is not used[/yellow]")
    return None


def _download(path, digest, target):
    """Write the upstream file to `target`; False when no mirror gives the expected file in time."""
    deadline = time.monotonic() + DEADLINE
    for mirror in MIRRORS:
        if time.monotonic() > deadline:
            break
        url = mirror.format(commit=GOOGLE_FONTS_COMMIT, path=path)
        try:
            sha256, size, shown = hashlib.sha256(), 0, 0
            with requests.get(url, stream=True, timeout=(10, 60)) as response, open(target, "wb") as handle:
                response.raise_for_status()
                total = int(response.headers.get("Content-Length") or 0)
                for chunk in response.iter_content(1 << 16):
                    check_cancel()
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"not complete after {DEADLINE} s")
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("larger than expected")
                    sha256.update(chunk)
                    handle.write(chunk)
                    if size - shown >= 4 * MB:
                        shown = size
                        rprint(f"[cyan]   {size / MB:.0f} MB" + (f" of {total / MB:.0f} MB" if total else "") + "[/cyan]")
            if sha256.hexdigest() == digest:
                return True
            rprint(f"[yellow]⚠️ {url} is not the expected file (SHA-256 {sha256.hexdigest()})[/yellow]")
        except (requests.RequestException, OSError, ValueError) as error:
            rprint(f"[yellow]⚠️ Could not download {url}: {escape(str(error))}[/yellow]")
    return False


def fetch(family):
    """Download (or take from fonts/) and build one face into fonts/. Returns True when it is there afterwards."""
    if os.path.isfile(font_path(family)):
        return True
    path, digest, upstream = DOWNLOADS[family]
    local = local_source(family)
    failed = _FAILED.get(family)
    if local is None and failed is not None and time.monotonic() - failed < RETRY_AFTER:
        wait = (RETRY_AFTER - (time.monotonic() - failed)) / 60
        rprint(f"[yellow]⚠️ The subtitle font {family} could not be downloaded just now, trying again in {wait:.0f} min[/yellow]")
        return False
    os.makedirs(FONTS_DIR, exist_ok=True)
    source = built = None
    try:
        # Next to the target so that os.replace is atomic; not .ttf so that nothing loads a half-written file
        handle, built = tempfile.mkstemp(prefix=".build-", suffix=".part", dir=FONTS_DIR)
        os.close(handle)
        if local:
            rprint(f"[cyan]🔤 Building the subtitle font {family} from {escape(local)}...[/cyan]")
        else:
            rprint(f"[cyan]🔤 Downloading the subtitle font {family} (once, 10-20 MB)...[/cyan]")
            handle, source = tempfile.mkstemp(prefix=".download-", suffix=".part", dir=FONTS_DIR)
            os.close(handle)
            if not _download(path, digest, source):
                _FAILED[family] = time.monotonic()
                rprint(
                    f"[yellow]⚠️ Could not download the subtitle font {family}. Without a network, put "
                    f"{escape(' or '.join(local_names(family)))} ({upstream} from GitHub google/fonts or "
                    f"fonts.google.com) in {escape(FONTS_DIR)}[/yellow]"
                )
                return False
        try:
            book(local or source, upstream, upstream.replace(" ", "")).save(built)
        except Exception as error:  # fontTools missing or a broken file: burn without the typesetter
            rprint(f"[yellow]⚠️ Could not build the subtitle font {family}: {escape(str(error))}[/yellow]")
            return False
        os.chmod(built, 0o644)  # mkstemp makes it readable by its owner only
        os.replace(built, font_path(family))
        _FAILED.pop(family, None)
        rprint(f"[green]✅ Subtitle font {family} saved to {escape(font_path(family))}[/green]")
        return True
    finally:
        for leftover in (source, built):
            if leftover and os.path.exists(leftover):
                os.remove(leftover)


def ensure(families):
    """Fetch whatever of `families` is missing. Returns True when all of them can be used.

    Stops at the first one that can not be had: the subtitles are then burnt without the typesetter anyway.
    """
    return all(fetch(family) for family in missing(families))
