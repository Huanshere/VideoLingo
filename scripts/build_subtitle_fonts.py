"""Rebuild the subtitle faces in fonts/ that are derived from upstream variable fonts.

    pip install fonttools==4.68.0
    git clone https://github.com/google/fonts && git -C fonts checkout 5bb28733cec313b63fbd415b574b5ae35c8aa8b8
    python scripts/build_subtitle_fonts.py path/to/google/fonts [output directory]

Without an output directory nothing is written: every face is rebuilt in memory and compared,
table by table, with the file in fonts/. With one, the faces are written there. The Chinese and
Japanese faces are not in the repository; core/utils/subtitle_fonts.py builds them on first use
with the same recipe, and they are compared too when they are in fonts/.

Why derived faces at all: libass picks a face by family name and asks for weight 400, so a
variable font is drawn at its default instance (Regular, normal width), and it takes the line
height from usWinAscent + usWinDescent, which upstream sets to hold every stacked mark of the
script. Each face here is one static instance under a family name of its own, with the vertical
metrics the sizes in core/utils/typeset.py were chosen against.
"""
import hashlib
import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
sys.path.insert(0, str(ROOT))
from core.utils.subtitle_fonts import DOWNLOADS, book, set_names  # noqa: E402

# Source files in a google/fonts checkout, with the SHA-256 they have at the commit above.
SOURCES = {
    "ofl/notosans/NotoSans[wdth,wght].ttf":
        "bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d",
    "ofl/roboto/Roboto[wdth,wght].ttf":
        "d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134",
    "ofl/notosansthai/NotoSansThai[wdth,wght].ttf":
        "5a1c559bb539583c8a1fd99d1c5b9491e5e14478c9cd2bd0970d5c3096cc9ef8",
    "ofl/notosansdevanagari/NotoSansDevanagari[wdth,wght].ttf":
        "14ec4af41f27482216d1c2229f417ff9b1425e1babb014e57d1d40d03229853e",
    "ofl/notosansarabic/NotoSansArabic[wdth,wght].ttf":
        "63111b5b2e074dd48cc67692e0a2726d86ee94c1c37fe8598257b7b4e87e869e",
    "ofl/notosanshebrew/NotoSansHebrew[wdth,wght].ttf":
        "7ef36a2c3593758cdb622e1bdef4f84523e92fbc3ccc667438dd80ff54c2de88",
    "ofl/notosansbengali/NotoSansBengali[wdth,wght].ttf":
        "dcd42978094e584a849c84a51450eeac40c8826057d566ea6d4b9627a403a05a",
    "ofl/notosanstamil/NotoSansTamil[wdth,wght].ttf":
        "aa3a9b321f4b0bb2c40203ffbde9af89713227866e0e13f76e5b9eeea727cf88",
    "ofl/notosanstelugu/NotoSansTelugu[wdth,wght].ttf":
        "e618af7bf999df192ed4f388eba2e563f2b5015034e9cbb317b5bd793bd7334d",
    "ofl/notosanskannada/NotoSansKannada[wdth,wght].ttf":
        "cca4f3b3a8cb12fb261f1b43baf5d2f7f59d90fe123d41f0065ed3a183997ec9",
    "ofl/notosansmalayalam/NotoSansMalayalam[wdth,wght].ttf":
        "312e0e7c3cc15fa09eb42a8f749eeb246b593ed420e3c81aafe8d910c3a6fb56",
    "ofl/notosansgujarati/NotoSansGujarati[wdth,wght].ttf":
        "9901d8552f1dd5d2c50dbd4caa6f6e174e74e8264f06594ab259ae6e7b1ac428",
    "ofl/notosansgurmukhi/NotoSansGurmukhi[wdth,wght].ttf":
        "1e6f728fa620e566f842d81e220265813faa12771214765d289c98e035adc5f2",
    "ofl/notosansoriya/NotoSansOriya[wdth,wght].ttf":
        "910342275d619081b896b4ed25fd9ad6ff320c25591b810de1fcc4beb153ba82",
    "ofl/notosanssinhala/NotoSansSinhala[wdth,wght].ttf":
        "9bd93e407a278075be403324063bc94a7e306c44de4df81214e932330c22eecf",
    "ofl/notosanskhmer/NotoSansKhmer[wdth,wght].ttf":
        "f37a8431a0c5d5ed2f81a767417546aca576a81fb7eff9c924d46aecf828f2ca",
    "ofl/notosanslao/NotoSansLao[wdth,wght].ttf":
        "9608b94603a82d09a8038946f9775242f99e3b3459b7f1e4d5b335b578cd7ab3",
    "ofl/notosansmyanmar/NotoSansMyanmar[wdth,wght].ttf":
        "7abbbfbe2514105d7ce94937aee3feb2ba89b73a256c8b77b5866bd9b83e32ec",
}
# The faces fetched on first use: file in fonts/ -> (source in the checkout, upstream family)
BOOK_FACES = {}
for _family, (_path, _digest, _upstream) in DOWNLOADS.items():
    _source = "ofl/" + _path.replace("%5B", "[").replace("%5D", "]")
    SOURCES[_source] = _digest
    BOOK_FACES[f"{_upstream.replace(' ', '')}-Book.ttf"] = (_source, _upstream)

# Script: (width axis, ascent, descent). The widest scripts are condensed further so that a
# line of ordinary length stays on one or two rows. Ascent and descent are in font units: the
# height of ordinary shaped text plus 0.06 em on each side, at least 0.92 em and 0.25 em.
LONG_TAIL = {
    "Thai": (87.5, 1077, 325),  # 1000 units per em
    "Devanagari": (87.5, 956, 250),  # 1000 units per em
    "Arabic": (87.5, 1003, 490),  # 1000 units per em
    "Hebrew": (87.5, 920, 250),  # 1000 units per em
    "Bengali": (87.5, 979, 250),  # 1000 units per em
    "Tamil": (75.0, 920, 381),  # 1000 units per em
    "Telugu": (87.5, 920, 481),  # 1000 units per em
    "Kannada": (87.5, 920, 430),  # 1000 units per em
    "Malayalam": (75.0, 920, 381),  # 1000 units per em
    "Gujarati": (87.5, 956, 328),  # 1000 units per em
    "Gurmukhi": (87.5, 956, 349),  # 1000 units per em
    "Oriya": (87.5, 1032, 317),  # 1000 units per em
    "Sinhala": (75.0, 1035, 331),  # 1000 units per em
    "Khmer": (87.5, 1035, 595),  # 1000 units per em
    "Lao": (87.5, 1178, 346),  # 1000 units per em
    "Myanmar": (75.0, 1063, 555),  # 1000 units per em
}


def set_line(font, ascent, descent, typo_metrics=False):
    """The line libass sets the face on: FontSize is scaled to ascent + descent."""
    os2, hhea = font["OS/2"], font["hhea"]
    os2.usWinAscent, os2.usWinDescent = ascent, descent
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ascent, -descent, 0
    hhea.ascent, hhea.descent, hhea.lineGap = ascent, -descent, 0
    if typo_metrics:
        os2.fsSelection |= 1 << 7


def reloaded(font):
    data = io.BytesIO()
    font.save(data)
    data.seek(0)
    return TTFont(data)


def latin(source, location, family, line, without=()):
    """Latin, Cyrillic and Greek of one row: a condensed instance of a two-axis family."""
    font = TTFont(source)
    pinned = {axis.axisTag: axis.defaultValue for axis in font["fvar"].axes}
    pinned.update(location)
    font = instancer.instantiateVariableFont(font, pinned, updateFontNames=False)
    postscript = family.replace(" ", "")
    set_names(font, ((1, family), (2, "Regular"), (3, f"{postscript};vl-latin"), (4, family), (6, postscript)))
    if "STAT" in font:
        del font["STAT"]
    set_line(font, *line)
    font["OS/2"].usWeightClass = 500
    if without:
        font = drop_blocks(reloaded(font), without)
    return font


def drop_blocks(font, blocks):
    """Leave these blocks to the face made for their script: fontconfig would offer this one first."""
    options = subset.Options()
    options.layout_features = options.layout_scripts = ["*"]
    options.name_IDs = options.name_languages = ["*"]
    options.name_legacy = options.notdef_outline = options.glyph_names = True
    options.legacy_kern = options.hinting = options.prune_unicode_ranges = True
    options.drop_tables = []
    options.passthrough_tables = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(
        unicodes=[code for code in font.getBestCmap() if not any(first <= code <= last for first, last in blocks)]
    )
    subsetter.subset(font)
    return font


def long_tail(source, script, width, ascent, descent):
    """One script of the Noto Sans family at weight 500, condensed like the Latin beside it."""
    font = instancer.instantiateVariableFont(TTFont(source), {"wght": 500, "wdth": width}, updateFontNames=False)
    for tag in ("STAT", "avar", "fvar", "gvar", "HVAR", "MVAR", "cvar"):
        if tag in font:
            del font[tag]
    font["OS/2"].usWeightClass = 500
    family, postscript = f"VL Noto Sans {script}", f"VLNotoSans{script}-Medium"
    name = font["name"]
    for record in list(name.names):
        if record.nameID >= 256:  # names of the instances that no longer exist
            name.names.remove(record)
    note = f"static wght500 wdth{width} from NotoSans{script} VF"
    set_names(
        font,
        ((1, family), (2, "Regular"), (3, f"{postscript};{note}"), (4, family), (6, postscript)),
        drop=(16, 17, 21, 22, 25),
    )
    font = reloaded(font)
    set_line(font, ascent, descent, typo_metrics=True)
    return font


def faces(checkout, out_dir_wanted=False):
    def source(path):
        file = Path(checkout) / path
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if digest != SOURCES[path]:
            raise SystemExit(f"{path} is not the file these faces were built from (SHA-256 {digest})")
        return file

    devanagari = ((0x0900, 0x097F), (0xA8E0, 0xA8FF), (0x1CD0, 0x1CFF))
    yield "VLNotoSansXCondMain.ttf", latin(
        source("ofl/notosans/NotoSans[wdth,wght].ttf"), {"wdth": 62.5, "wght": 550},
        "VL Noto Sans XCond Main", (1050, 270), without=devanagari,
    )
    yield "VLRobotoCondSub.ttf", latin(
        source("ofl/roboto/Roboto[wdth,wght].ttf"), {"wdth": 75, "wght": 500}, "VL Roboto Cond Sub", (1926, 437)
    )
    for script, (width, ascent, descent) in LONG_TAIL.items():
        path = f"ofl/notosans{script.lower()}/NotoSans{script}[wdth,wght].ttf"
        yield f"VLNotoSans{script}-Medium.ttf", long_tail(source(path), script, width, ascent, descent)
    for filename, (path, upstream) in BOOK_FACES.items():
        if out_dir_wanted or (FONTS / filename).exists():
            yield filename, book(source(path), upstream, upstream.replace(" ", ""))


def differing_tables(built, shipped):
    """Tables that are not byte for byte the same; `head` holds the time the file was saved."""
    built, shipped = reloaded(built), TTFont(shipped)
    tags = set(built.keys()) | set(shipped.keys())
    return sorted(
        tag for tag in tags - {"head", "GlyphOrder"}
        if tag not in built or tag not in shipped or built.getTableData(tag) != shipped.getTableData(tag)
    )


def main(checkout, out_dir=None):
    failed = False
    for filename, font in faces(checkout, bool(out_dir)):
        if out_dir:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            font.save(str(Path(out_dir) / filename))
            print("wrote", filename)
            continue
        different = differing_tables(font, FONTS / filename)
        failed = failed or bool(different)
        print(filename, "differs in " + ", ".join(different) if different else "matches the file in fonts/")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    raise SystemExit(main(*sys.argv[1:]))
