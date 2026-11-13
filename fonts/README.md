# Subtitle fonts

`core/utils/typeset.py` sets every burned-in subtitle line in a face chosen for
its writing system and for its row: the translation is the yellow boxed row on
top, the source is the white outlined row under it. ffmpeg's `ass` filter finds
the faces here by family name (`ass=...:fontsdir=fonts`), so nothing has to be
installed on the system.

Nineteen faces are in the repository. The four Chinese and Japanese faces are
10 MB or more each, so `core/utils/subtitle_fonts.py` downloads them the first
time a video needs one (see below). When a face can not be had, or a font name
is set in `subtitle.style`, the subtitles are burned the old way with the
`subtitles` filter and the fonts of the system.

## Which face draws what

Sizes are ASS `FontSize` on a 288-row grid of the frame's short side, the same
grid as the 15 / 17 of `subtitle.style` (whose `font_size` scales them). libass
scales a face until `usWinAscent + usWinDescent` equals `FontSize`, so the same
number is a different visible size in every face. The sizes were set by eye
against the English source row and the Chinese translation row.

| Writing system | Translation row | Source row |
| --- | --- | --- |
| Chinese, Simplified | Noto Sans SC Book 23.7, spacing 0.9 | Noto Sans SC Book 19.4, spacing 0.4 |
| Chinese, Traditional | Noto Sans TC Book 23.7, spacing 0.9 | Noto Sans TC Book 19.4, spacing 0.4 |
| Cantonese | Noto Sans HK Book 23.7, spacing 0.9 | Noto Sans HK Book 19.4, spacing 0.4 |
| Japanese | Noto Sans JP Book 23.8, spacing 0.5 | Noto Sans JP Book 19.4, spacing 0.4 |
| Korean | Pretendard Medium 21.2, spacing 0.25 | Pretendard Medium 17.3, spacing 0.25 |
| Latin, Cyrillic, Greek | VL Noto Sans XCond Main 22 | VL Roboto Cond Sub 18 at 96 % width |
| Thai | VL Noto Sans Thai 25.11 | VL Noto Sans Thai 23.36 |
| Devanagari | VL Noto Sans Devanagari 22.4 | VL Noto Sans Devanagari 20.84 |
| Arabic, Persian, Urdu | VL Noto Sans Arabic 27.72 | VL Noto Sans Arabic 25.79 |
| Hebrew | VL Noto Sans Hebrew 19.4 | VL Noto Sans Hebrew 18.05 |
| Bengali | VL Noto Sans Bengali 22.41 | VL Noto Sans Bengali 20.85 |
| Tamil | VL Noto Sans Tamil 21.58 | VL Noto Sans Tamil 20.07 |
| Telugu | VL Noto Sans Telugu 24.39 | VL Noto Sans Telugu 22.69 |
| Kannada | VL Noto Sans Kannada 23.51 | VL Noto Sans Kannada 21.87 |
| Malayalam | VL Noto Sans Malayalam 21.58 | VL Noto Sans Malayalam 20.07 |
| Gujarati | VL Noto Sans Gujarati 22.99 | VL Noto Sans Gujarati 21.39 |
| Gurmukhi | VL Noto Sans Gurmukhi 22.73 | VL Noto Sans Gurmukhi 21.14 |
| Odia | VL Noto Sans Oriya 23.49 | VL Noto Sans Oriya 21.85 |
| Sinhala | VL Noto Sans Sinhala 22.65 | VL Noto Sans Sinhala 21.07 |
| Khmer | VL Noto Sans Khmer 28.38 | VL Noto Sans Khmer 26.4 |
| Lao | VL Noto Sans Lao 27.8 | VL Noto Sans Lao 25.86 |
| Burmese | VL Noto Sans Myanmar 28.18 | VL Noto Sans Myanmar 26.21 |

A word of another script inside a line (a product name in a Hindi sentence, a
Chinese name in an English one) is drawn by the face of its own script, at the
size that script has on that row.

There is no face for Armenian, Georgian, Ethiopic or Tibetan. Those fall back
through fontconfig to whatever the system has, as they did before.

## Where the files come from

Every face but Pretendard is a static instance cut from a variable font in
[google/fonts](https://github.com/google/fonts) at commit
`5bb28733cec313b63fbd415b574b5ae35c8aa8b8`. `scripts/build_subtitle_fonts.py`
holds the recipe and the SHA-256 of every source file. Run without an output
directory it rebuilds each face in memory and compares it with the file here,
table by table:

```bash
pip install fonttools==4.68.0
git clone https://github.com/google/fonts
git -C fonts checkout 5bb28733cec313b63fbd415b574b5ae35c8aa8b8
python scripts/build_subtitle_fonts.py fonts
```

All of them come out the same in every table but `head`, which stores the time
the file was saved.

Why instances and not the variable fonts themselves: libass finds a face by
family name, asks for weight 400 and draws the default instance of a variable
font, which is Regular at normal width (Thin for Noto Sans Hebrew). It also
takes the line height from `usWinAscent + usWinDescent`, which upstream sets
tall enough for every stacked mark a script can produce, so the letters come
out small and the rows far apart. Each instance has one weight and one width,
the vertical metrics the sizes above were chosen against, and a family name of
its own so it is never confused with an installed Noto Sans.

| File | Family name | Cut from | Instance |
| --- | --- | --- | --- |
| `VLNotoSansXCondMain.ttf` | VL Noto Sans XCond Main | `ofl/notosans/NotoSans[wdth,wght].ttf` | `wdth` 62.5, `wght` 550, without the Devanagari blocks |
| `VLRobotoCondSub.ttf` | VL Roboto Cond Sub | `ofl/roboto/Roboto[wdth,wght].ttf` | `wdth` 75, `wght` 500 |
| `VLNotoSans<Script>-Medium.ttf` | VL Noto Sans \<Script\> | `ofl/notosans<script>/NotoSans<Script>[wdth,wght].ttf` | `wght` 500; `wdth` 75 for Tamil, Malayalam, Sinhala and Myanmar, 87.5 for the other twelve |
| `NotoSans{SC,TC,HK,JP}-Book.ttf` | Noto Sans SC / TC / HK / JP Book | `ofl/notosans{sc,tc,hk,jp}/NotoSans{SC,TC,HK,JP}[wght].ttf` | `wght` 450, downloaded on first use |

Noto Sans carries a copy of Devanagari that is older than the one in Noto Sans
Devanagari. It is removed from VL Noto Sans XCond Main so that a Hindi word in
an English line is drawn by the Devanagari face.

`Pretendard-Medium.otf` is `public/static/Pretendard-Medium.otf` of release
v1.3.9 of [orioncactus/pretendard](https://github.com/orioncactus/pretendard),
unmodified.

### Downloaded on first use

`core/utils/subtitle_fonts.py` fetches the variable font from GitHub (jsDelivr
as a second mirror), checks its SHA-256, cuts the `wght` 450 instance and saves
it here. It does that only for the faces a video's subtitles need, once.
`.gitignore` keeps the results out of commits.

| Saved as | Source file | Source bytes | Source SHA-256 |
| --- | --- | ---: | --- |
| `NotoSansSC-Book.ttf` | `ofl/notosanssc/NotoSansSC[wght].ttf` | 17.8 MB | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| `NotoSansTC-Book.ttf` | `ofl/notosanstc/NotoSansTC[wght].ttf` | 11.9 MB | `864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f` |
| `NotoSansHK-Book.ttf` | `ofl/notosanshk/NotoSansHK[wght].ttf` | 11.9 MB | `76098ee78ec234cd4f8c950742b3f766fea2f8b43d5180d901048f4fc86c6849` |
| `NotoSansJP-Book.ttf` | `ofl/notosansjp/NotoSansJP[wght].ttf` | 9.6 MB | `c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f` |

Without a network (or behind a firewall that blocks both mirrors) put the four
files here yourself, built with `scripts/build_subtitle_fonts.py` from a
google/fonts checkout and an output directory.

## Licences

- Noto Sans, the sixteen Noto Sans script families and Roboto: SIL Open Font
  License 1.1, no reserved font name. `OFL-NotoSans.txt`, `OFL-Roboto.txt`,
  `OFL-NotoSans<Script>.txt`.
- Noto Sans SC, TC, HK and JP: SIL Open Font License 1.1 with the reserved
  font name "Source". The instances keep the Noto Sans family name.
  `OFL-NotoSansSC.txt`, `OFL-NotoSansTC.txt`, `OFL-NotoSansHK.txt`,
  `OFL-NotoSansJP.txt`.
- Pretendard: SIL Open Font License 1.1 with a reserved font name, shipped
  unmodified. `OFL-Pretendard.txt`.

## Sizes

| File | Family name | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `Pretendard-Medium.otf` | Pretendard Medium | 1584068 | `d39e50e4bb52b4993b6a4eeb821a171254745bd824446af01e1f616b89fface0` |
| `VLNotoSansArabic-Medium.ttf` | VL Noto Sans Arabic | 194272 | `85e64ccfb7545c432209dd65c036fc7533c4bd81ca7db245471d4764968d5a25` |
| `VLNotoSansBengali-Medium.ttf` | VL Noto Sans Bengali | 141500 | `4bb9cf0a10067c7529e5af82f8af3cd12d06ba05ca37cfe8f8a949180a2f1a6d` |
| `VLNotoSansDevanagari-Medium.ttf` | VL Noto Sans Devanagari | 218556 | `49ccdf692dbb4d170d1df82d71c668e673dc499958990ecd30b0bea41cfcd4da` |
| `VLNotoSansGujarati-Medium.ttf` | VL Noto Sans Gujarati | 178968 | `43e37c3239f3e26547331655ead4ff3752f96a79f4cd8804b7c343ec76516561` |
| `VLNotoSansGurmukhi-Medium.ttf` | VL Noto Sans Gurmukhi | 67392 | `f4891c5fa9bb33eac477662b7a53a692174dac037698dadc0be4387c71a30706` |
| `VLNotoSansHebrew-Medium.ttf` | VL Noto Sans Hebrew | 47556 | `5cb1507d98cb22eedd49ffdc83027142a26f30e6a9e8ce9a0a9a3c40fe9ac533` |
| `VLNotoSansKannada-Medium.ttf` | VL Noto Sans Kannada | 169316 | `5e13187b83201e872c00da64474dfbebd363455094a55c2ee2d3fdb3e2280357` |
| `VLNotoSansKhmer-Medium.ttf` | VL Noto Sans Khmer | 105832 | `e095bb158f6bcf75c9ae0eb7529368e06d3bcdcc1ecb7666bd2b6ce089c27f22` |
| `VLNotoSansLao-Medium.ttf` | VL Noto Sans Lao | 52656 | `479e5913fcacd9fd2e07ab0917876553d600b96300d2fb260e12385f0371e0a5` |
| `VLNotoSansMalayalam-Medium.ttf` | VL Noto Sans Malayalam | 111460 | `469edd077dbf4646208ebbdfe602febea0215dda2fb7a73da095bafda20d3a22` |
| `VLNotoSansMyanmar-Medium.ttf` | VL Noto Sans Myanmar | 187152 | `9e209450dd36e5f1f5dfc70f37a7f609fde7e137ba7b8339b6ee983c30eed8c0` |
| `VLNotoSansOriya-Medium.ttf` | VL Noto Sans Oriya | 171620 | `3733413eeb45ec0c7219525194d7cbb4ae85dc5a48794c1c9c555be569babdcf` |
| `VLNotoSansSinhala-Medium.ttf` | VL Noto Sans Sinhala | 247032 | `9e9701797dc4535e3a6a6a2d107698d879c2847edcfba1965b24fb7a9d207bfe` |
| `VLNotoSansTamil-Medium.ttf` | VL Noto Sans Tamil | 82608 | `81a1f5115285f5b52c6c542a5fe706ebaf1b35eece13f0c6e992a02cd1bbd9e4` |
| `VLNotoSansTelugu-Medium.ttf` | VL Noto Sans Telugu | 209272 | `96a6a33b8d95e11f3b519ba848fef40f84b9d171c134e97ed5436f654131fac3` |
| `VLNotoSansThai-Medium.ttf` | VL Noto Sans Thai | 47484 | `d5a48c3b263aac59edc4dab810906c36f1a06a3d22eefdec17a5162a1125d0e7` |
| `VLNotoSansXCondMain.ttf` | VL Noto Sans XCond Main | 448768 | `f3bc19202e0eee094b654b28a565416194a6811d77d2e5e61a1022b9b5fa58f6` |
| `VLRobotoCondSub.ttf` | VL Roboto Cond Sub | 157388 | `d8876b3468f5326f86dc2957c07c3704785e062d2980900a2156293b56fc40f8` |

4.4 MB in the repository. The four downloaded faces take 30.6 MB once all of
them are there; most videos need one.
