"""Tests of the subtitle typesetter (core/utils/typeset.py): which font a language gets, where lines break, what libass draws."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pytest

pytest.importorskip("uharfbuzz", reason="the subtitle typesetter needs uharfbuzz (requirements.txt)")

from core.utils import subtitle_fonts, typeset  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN, SECONDARY = typeset.MAIN, typeset.SECONDARY

# language: (script, style, a line of ordinary length, a long line)
SAMPLES = {
    "en": (
        "latin", "latin",
        "It was created in 1995 by Brendan Eich in just ten days.",
        "Today it runs on billions of devices all around the world, from web browsers to servers and even smartphones.",
    ),
    "de": (
        "latin", "latin",
        "Es wurde 1995 von Brendan Eich in nur zehn Tagen entwickelt.",
        "Heute läuft es weltweit auf Milliarden von Geräten, von Webbrowsern über Server bis hin zu den Smartphones in unseren Hosentaschen.",
    ),
    "fr": (
        "latin", "latin",
        "Il a été créé en 1995 par Brendan Eich en seulement dix jours.",
        "Aujourd’hui, il tourne sur des milliards d’appareils dans le monde entier, des navigateurs web aux serveurs et aux smartphones.",
    ),
    "es": (
        "latin", "latin",
        "Fue creado en 1995 por Brendan Eich en tan solo diez días.",
        "Hoy se ejecuta en miles de millones de dispositivos en todo el mundo, desde navegadores web hasta servidores y teléfonos inteligentes.",
    ),
    "it": (
        "latin", "latin",
        "È stato creato nel 1995 da Brendan Eich in soli dieci giorni.",
        "Oggi gira su miliardi di dispositivi in tutto il mondo, dai browser web ai server fino agli smartphone che abbiamo in tasca.",
    ),
    "pt": (
        "latin", "latin",
        "Foi criado em 1995 por Brendan Eich em apenas dez dias.",
        "Hoje ele roda em bilhões de dispositivos, de navegadores a servidores e celulares.",
    ),
    "vi": (
        "latin", "latin",
        "Nó được Brendan Eich tạo ra vào năm 1995 chỉ trong mười ngày.",
        "Ngày nay nó chạy trên hàng tỷ thiết bị, từ trình duyệt web đến máy chủ và điện thoại.",
    ),
    "pl": (
        "latin", "latin",
        "Został stworzony w 1995 roku przez Brendana Eicha w zaledwie dziesięć dni.",
        "Dziś działa na miliardach urządzeń, od przeglądarek po serwery i telefony.",
    ),
    "tr": (
        "latin", "latin",
        "1995 yılında Brendan Eich tarafından yalnızca on günde yaratıldı.",
        "Bugün web tarayıcılarından sunuculara ve telefonlara, milyarlarca cihazda çalışıyor.",
    ),
    "ru": (
        "cyrillic", "cyrillic",
        "Его создал Брендан Эйх в 1995 году всего за десять дней.",
        "Сегодня он работает на миллиардах устройств по всему миру — от веб-браузеров до серверов и смартфонов в наших карманах.",
    ),
    "zh": (
        "zh", "zh",
        "它由 Brendan Eich 在 1995 年仅用十天创造出来",
        "如今它运行在全世界数十亿台各种各样的设备上 从网页浏览器到服务器 甚至再到我们每个人口袋里的智能手机",
    ),
    "zh-TW": (
        "zh", "zh-hant",
        "它由 Brendan Eich 在 1995 年僅用十天創造出來",
        "如今它運行在全世界數十億台各式各樣的裝置上 從網頁瀏覽器到伺服器 甚至再到我們每個人口袋裡的智慧型手機",
    ),
    "yue": (
        "zh", "yue",
        "佢係 Brendan Eich 喺 1995 年淨係用咗十日整出嚟嘅",
        "而家佢喺全世界幾十億部各種各樣嘅裝置上面行緊 由網頁瀏覽器到伺服器 甚至乎我哋每個人袋入面部智能手機都係",
    ),
    "ja": (
        "ja", "ja",
        "1995 年にブレンダン・アイクがわずか 10 日間で作りました",
        "今では世界中のウェブブラウザからサーバー、そして私たちのポケットの中のスマートフォンまで、数十億台ものデバイスで動いています",
    ),
    "ko": (
        "ko", "ko",
        "1995년 브렌던 아이크가 단 열흘 만에 만들었습니다",
        "오늘날에는 전 세계의 웹 브라우저부터 서버, 그리고 우리 주머니 속 스마트폰까지 수십억 대의 다양한 기기에서 실행되고 있습니다",
    ),
    "th": (
        "thai", "thai",
        "มันถูกสร้างขึ้นในปี 1995 โดยเบรนแดน ไอค์ ภายในเวลาเพียงสิบวัน",
        "ทุกวันนี้มันทำงานบนอุปกรณ์หลายพันล้านเครื่อง ตั้งแต่เว็บเบราว์เซอร์ไปจนถึงเซิร์ฟเวอร์และโทรศัพท์",
    ),
    "hi": (
        "devanagari", "devanagari",
        "इसे 1995 में ब्रेंडन आइक ने सिर्फ़ दस दिनों में बनाया था।",
        "आज यह अरबों उपकरणों पर चलता है, वेब ब्राउज़र से लेकर सर्वर और फ़ोन तक।",
    ),
    "ar": (
        "arabic", "arabic",
        "أنشأه بريندان آيك عام 1995 في عشرة أيام فقط.",
        "اليوم يعمل على مليارات الأجهزة، من متصفحات الويب إلى الخوادم والهواتف.",
    ),
    "fa": (
        "arabic", "arabic",
        "این زبان در سال ۱۹۹۵ توسط برندن آیک تنها در ده روز ساخته شد.",
        "امروزه روی میلیاردها دستگاه اجرا می‌شود، از مرورگرهای وب تا سرورها و تلفن‌ها.",
    ),
    "ur": (
        "arabic", "arabic",
        "اسے 1995 میں برینڈن آئیک نے صرف دس دنوں میں بنایا تھا۔",
        "آج یہ ویب براؤزرز سے لے کر سرورز اور فونز تک اربوں آلات پر چلتا ہے۔",
    ),
    "he": (
        "hebrew", "hebrew",
        "הוא נוצר בשנת 1995 על ידי Brendan Eich בתוך עשרה ימים בלבד.",
        "כיום הוא פועל במיליארדי מכשירים, מדפדפני אינטרנט ועד שרתים וטלפונים.",
    ),
    "bn": (
        "bengali", "bengali",
        "১৯৯৫ সালে ব্রেন্ডান আইক মাত্র দশ দিনে এটি তৈরি করেন।",
        "আজ এটি কোটি কোটি ডিভাইসে চলে, ওয়েব ব্রাউজার থেকে সার্ভার ও ফোন পর্যন্ত।",
    ),
    "ta": (
        "tamil", "tamil",
        "இது 1995 இல் பிரெண்டன் ஐக் என்பவரால் வெறும் பத்து நாட்களில் உருவாக்கப்பட்டது.",
        "இன்று இது இணைய உலாவிகள் முதல் சேவையகங்கள், தொலைபேசிகள் வரை பல கோடி சாதனங்களில் இயங்குகிறது.",
    ),
    "te": (
        "telugu", "telugu",
        "దీనిని 1995లో బ్రెండన్ ఐక్ కేవలం పది రోజుల్లో సృష్టించారు.",
        "ఈ రోజు ఇది వెబ్ బ్రౌజర్ల నుండి సర్వర్లు, ఫోన్ల వరకు కోట్లాది పరికరాలపై నడుస్తుంది.",
    ),
    "kn": (
        "kannada", "kannada",
        "ಇದನ್ನು 1995 ರಲ್ಲಿ ಬ್ರೆಂಡನ್ ಐಕ್ ಕೇವಲ ಹತ್ತು ದಿನಗಳಲ್ಲಿ ರಚಿಸಿದರು.",
        "ಇಂದು ಇದು ವೆಬ್ ಬ್ರೌಸರ್‌ಗಳಿಂದ ಸರ್ವರ್‌ಗಳು ಮತ್ತು ಫೋನ್‌ಗಳವರೆಗೆ ಶತಕೋಟಿ ಸಾಧನಗಳಲ್ಲಿ ಚಲಿಸುತ್ತದೆ.",
    ),
    "ml": (
        "malayalam", "malayalam",
        "1995-ൽ ബ്രെൻഡൻ ഐക്ക് വെറും പത്ത് ദിവസം കൊണ്ടാണ് ഇത് സൃഷ്ടിച്ചത്.",
        "ഇന്ന് വെബ് ബ്രൗസറുകൾ മുതൽ സെർവറുകളും ഫോണുകളും വരെ കോടിക്കണക്കിന് ഉപകരണങ്ങളിൽ ഇത് പ്രവർത്തിക്കുന്നു.",
    ),
    "gu": (
        "gujarati", "gujarati",
        "તેને 1995માં બ્રેન્ડન આઈકે માત્ર દસ દિવસમાં બનાવ્યું હતું.",
        "આજે તે વેબ બ્રાઉઝરથી લઈને સર્વર અને ફોન સુધી અબજો ઉપકરણો પર ચાલે છે.",
    ),
    "pa": (
        "gurmukhi", "gurmukhi",
        "ਇਸਨੂੰ 1995 ਵਿੱਚ ਬ੍ਰੈਂਡਨ ਆਈਕ ਨੇ ਸਿਰਫ਼ ਦਸ ਦਿਨਾਂ ਵਿੱਚ ਬਣਾਇਆ ਸੀ।",
        "ਅੱਜ ਇਹ ਵੈੱਬ ਬ੍ਰਾਊਜ਼ਰਾਂ ਤੋਂ ਲੈ ਕੇ ਸਰਵਰਾਂ ਅਤੇ ਫ਼ੋਨਾਂ ਤੱਕ ਅਰਬਾਂ ਡਿਵਾਈਸਾਂ ਉੱਤੇ ਚੱਲਦਾ ਹੈ।",
    ),
    "or": (
        "oriya", "oriya",
        "ଏହାକୁ 1995 ରେ ବ୍ରେଣ୍ଡନ୍ ଆଇକ୍ ମାତ୍ର ଦଶ ଦିନରେ ତିଆରି କରିଥିଲେ।",
        "ଆଜି ଏହା ୱେବ୍ ବ୍ରାଉଜରଠାରୁ ସର୍ଭର ଏବଂ ଫୋନ୍ ପର୍ଯ୍ୟନ୍ତ କୋଟି କୋଟି ଉପକରଣରେ ଚାଲେ।",
    ),
    "si": (
        "sinhala", "sinhala",
        "එය 1995 දී බ්‍රෙන්ඩන් අයික් විසින් දින දහයකින් නිර්මාණය කරන ලදී.",
        "අද එය වෙබ් බ්‍රව්සර්වල සිට සේවාදායක සහ දුරකථන දක්වා බිලියන ගණනක උපාංගවල ක්‍රියාත්මක වේ.",
    ),
    "km": (
        "khmer", "khmer",
        "វាត្រូវបានបង្កើតឡើងក្នុងឆ្នាំ 1995 ដោយ Brendan Eich ក្នុងរយៈពេលតែដប់ថ្ងៃប៉ុណ្ណោះ។",
        "សព្វថ្ងៃនេះ វាដំណើរការលើឧបករណ៍រាប់ពាន់លានគ្រឿង ចាប់ពីកម្មវិធីរុករកបណ្ដាញ រហូតដល់ម៉ាស៊ីនមេ និងទូរសព្ទ។",
    ),
    "lo": (
        "lao", "lao",
        "ມັນຖືກສ້າງຂຶ້ນໃນປີ 1995 ໂດຍ Brendan Eich ພາຍໃນເວລາພຽງສິບມື້.",
        "ທຸກມື້ນີ້ມັນເຮັດວຽກຢູ່ໃນອຸປະກອນຫຼາຍພັນລ້ານເຄື່ອງ ຕັ້ງແຕ່ເວັບບຣາວເຊີໄປຈົນເຖິງເຊີບເວີ ແລະ ໂທລະສັບ.",
    ),
    "my": (
        "myanmar", "myanmar",
        "၎င်းကို ၁၉၉၅ ခုနှစ်တွင် Brendan Eich က ဆယ်ရက်အတွင်း ဖန်တီးခဲ့သည်။",
        "ယနေ့တွင် ၎င်းသည် ဝဘ်ဘရောက်ဇာများမှ ဆာဗာများနှင့် ဖုန်းများအထိ စက်ပစ္စည်း ဘီလီယံပေါင်းများစွာတွင် အလုပ်လုပ်သည်။",
    ),
}

LANDSCAPE, PORTRAIT, SQUARE, FULL_HD = (854, 480), (480, 854), (480, 480), (1920, 1080)

# The Chinese and Japanese faces are downloaded on first use (core/utils/subtitle_fonts.py), they are
# not in the repository. Without them the tests that need them are skipped.
NOT_DOWNLOADED = subtitle_fonts.missing(subtitle_fonts.DOWNLOADS)
needs_downloads = unittest.skipIf(
    NOT_DOWNLOADED,
    f"fonts/ lacks {', '.join(NOT_DOWNLOADED)}, get them with: "
    'python -c "from core.utils import subtitle_fonts as f; f.ensure(f.DOWNLOADS)"',
)
# The languages whose faces are all in fonts/
AVAILABLE = {
    language: sample for language, sample in SAMPLES.items()
    if not subtitle_fonts.missing(typeset.track_family(role, sample[2:]) for role in (MAIN, SECONDARY))
}


def track_for(role, *texts):
    return typeset.plan_track(role, list(texts))


def typeset_line(text, role, size=LANDSCAPE, track=None):
    """One cue typeset on its own: (block, track)."""
    track = track or track_for(role, text)
    cue = typeset.Cue(0, 1000, typeset.clean_text(text))
    return typeset.typeset_cue(cue, track, typeset.geometry(*size)), track


def line_texts(block):
    return [
        "".join((" " if index and token.space_before else "") + token.text for index, token in enumerate(line))
        for line in block.lines
    ]


def srt(*texts, seconds=1):
    """Cues one after another, `seconds` long each."""
    def stamp(second):
        return f"00:{second // 60:02d}:{second % 60:02d},000"

    return "\n".join(
        f"{index + 1}\n{stamp(index * seconds)} --> {stamp((index + 1) * seconds)}\n{text}\n"
        for index, text in enumerate(texts)
    )


def cues(*texts):
    return typeset.parse_srt(srt(*texts))


def positions(script):
    """The \\pos of every event of an ASS script."""
    return [(float(x), float(y)) for x, y in re.findall(r"\\pos\(([\d.]+),([\d.]+)\)", script.text)]


class ScriptTests(unittest.TestCase):
    """Which writing system a track is in."""

    def test_every_language_is_recognised(self):
        for language, (script, style, ordinary, long) in SAMPLES.items():
            with self.subTest(language=language):
                self.assertEqual(typeset.classify([ordinary, long]), script)
                if script == "zh":
                    self.assertEqual(typeset.chinese_variant([ordinary, long]), style)
                if language in AVAILABLE:
                    for role in (MAIN, SECONDARY):
                        self.assertEqual(track_for(role, ordinary, long).key, style)

    def test_names_and_terms_in_another_script_do_not_decide(self):
        # An ideograph says about as much as two letters.
        chinese = ["JavaScript 是在十天之内创造出来的", "由 Brendan Eich 设计"]
        self.assertEqual(typeset.classify(chinese), "zh")
        self.assertEqual(typeset.classify(["Он написал JavaScript за десять дней"]), "cyrillic")
        self.assertEqual(typeset.classify(["The word 你好 means hello in Chinese."]), "latin")
        # Kanji alone are Chinese; a little kana makes the track Japanese.
        self.assertEqual(typeset.classify(["東京都は日本の首都です"]), "ja")
        self.assertEqual(typeset.classify(["東京都日本首都"]), "zh")

    def test_lines_without_letters_are_set_as_latin(self):
        self.assertEqual(typeset.classify(["123 !?", "♪♪"]), "latin")
        self.assertEqual(typeset.classify([]), "latin")

    def test_chinese_is_told_apart_by_its_characters(self):
        self.assertEqual(typeset.chinese_variant(["这是简体中文字幕"]), "zh")
        self.assertEqual(typeset.chinese_variant(["這是繁體中文字幕"]), "zh-hant")
        self.assertEqual(typeset.chinese_variant(["呢個係廣東話字幕，佢哋喺度睇緊嘢"]), "yue")
        # A stray traditional character in a simplified track changes nothing.
        self.assertEqual(typeset.chinese_variant(["这是简体中文字幕", "乾隆皇帝的故事", "还有很多简体字在这里"]), "zh")


class StyleTests(unittest.TestCase):
    """Which font and size a track is set in."""

    @needs_downloads
    def test_english_and_chinese_have_the_reference_look(self):
        chinese, english = SAMPLES["zh"][2], SAMPLES["en"][2]
        self.assertEqual(track_for(MAIN, chinese).style, typeset.Style("Noto Sans SC Book", 23.7, 0.9))
        self.assertEqual(track_for(SECONDARY, english).style, typeset.Style("VL Roboto Cond Sub", 18, 0.0, 0.96))
        # The other way round each row is set in the face of its language.
        self.assertEqual(track_for(MAIN, english).style, typeset.Style("VL Noto Sans XCond Main", 22))
        self.assertEqual(track_for(SECONDARY, chinese).style, typeset.Style("Noto Sans SC Book", 19.4, 0.4))

    def test_every_language_has_a_shipped_face_that_draws_it(self):
        for language, (script, style, ordinary, long) in AVAILABLE.items():
            for role in (MAIN, SECONDARY):
                with self.subTest(language=language, role=role):
                    track = track_for(role, ordinary, long)
                    self.assertTrue(os.path.isfile(track.face.path), track.face.path)
                    faces = [track.face]
                    if track.word_fallback:
                        faces.append(typeset.face_for(track.word_fallback.family))
                    native = {script, "zh"} if script == "ja" else {script}
                    missing = sorted({
                        char for char in ordinary + long
                        if typeset.script_class(char) in native and not any(face.covers(char) for face in faces)
                    })
                    self.assertEqual(missing, [])

    @needs_downloads
    def test_every_shipped_face_is_used_by_some_language(self):
        used = set()
        for language, (script, style, ordinary, long) in SAMPLES.items():
            for role in (MAIN, SECONDARY):
                track = track_for(role, ordinary, long)
                used.add(track.style.family)
                used.update(
                    extra.family for extra in (track.word_fallback, track.latin, track.latin_fallback) if extra
                )
        self.assertEqual(used, set(typeset.FONT_FILES))
        for family, filename in typeset.FONT_FILES.items():
            self.assertTrue((REPO_ROOT / "fonts" / filename).is_file(), filename)

    def test_the_translation_row_is_the_larger_one(self):
        for language, (script, style, ordinary, long) in SAMPLES.items():
            with self.subTest(language=language):
                main = typeset.style_for(MAIN, style).size
                secondary = typeset.style_for(SECONDARY, style).size
                self.assertGreater(main, secondary)
                self.assertLess(main, secondary * 1.3)

    def test_latin_and_cyrillic_source_rows_are_set_in_one_face(self):
        roboto = "VL Roboto Cond Sub"
        for language in ("en", "de", "fr", "es", "it", "pt", "ru", "vi", "pl", "tr"):
            self.assertEqual(track_for(SECONDARY, *SAMPLES[language][2:]).style.family, roboto, language)
        # A foreign name in an English video is set in the same face, not in a system font.
        english = [SAMPLES["en"][2]] * 20 + ["It was written by Wiśniewski and Dvořák."]
        block, track = typeset_line(english[-1], SECONDARY, track=typeset.plan_track(SECONDARY, english))
        families = {run.style.family for line in block.lines for token in line for run in token.runs}
        self.assertEqual(families, {roboto})

    def test_latin_inside_another_script_is_set_in_a_latin_face(self):
        block, track = typeset_line("यह JavaScript में लिखा गया है", SECONDARY)
        families = {run.style.family for line in block.lines for token in line for run in token.runs}
        self.assertEqual(families, {"VL Noto Sans Devanagari", "VL Roboto Cond Sub"})
        block, track = typeset_line("यह JavaScript में लिखा गया है", MAIN)
        families = {run.style.family for line in block.lines for token in line for run in token.runs}
        self.assertEqual(families, {"VL Noto Sans Devanagari", "VL Noto Sans XCond Main"})

    def test_missing_font_file_is_an_error_not_a_guess(self):
        shipped = typeset.FONTS_DIR
        self.addCleanup(typeset.reset_fonts, shipped)
        with tempfile.TemporaryDirectory() as empty:
            typeset.reset_fonts(empty)
            with self.assertRaisesRegex(RuntimeError, "font is missing"):
                track_for(MAIN, SAMPLES["zh"][2])


class SrtTests(unittest.TestCase):
    def test_srt_files_are_read_as_players_read_them(self):
        data = (
            "\ufeff1\r\n00:00:01,000 --> 00:00:02,500\r\n<i>Hello</i> {\\an8}world\r\n\r\n"
            "2\r\n00:00:02.000 --> 00:00:04.000\r\nsecond\r\nline\r\n"  # no blank line after it
            "3\r\n00:00:05,000 --> 00:00:06,000\r\n\r\n"                 # no text
            "4\r\n00:00:07,000 --> 00:00:06,000\r\nbackwards\r\n\r\n"    # ends before it starts
            "5\r\n00:00:08,000 --> 00:00:09,000\r\nlast\r\n"
        )
        self.assertEqual(
            typeset.parse_srt(data),
            [
                typeset.Cue(1000, 2000, "Hello world"),  # cut where the next one starts
                typeset.Cue(2000, 4000, "second line"),
                typeset.Cue(8000, 9000, "last"),
            ],
        )

    def test_markup_never_reaches_the_ass_script(self):
        self.assertEqual(typeset.clean_text('<font color="#fff">x</font>  y'), "x y")
        self.assertEqual(typeset.clean_text("a\\Nb"), "a b")
        self.assertEqual(typeset.clean_text("{\\pos(1,1)}z"), "z")
        scripts, _ = typeset.build_scripts(cues("{\\fs90}plain {braces} \\N stay"), [], *LANDSCAPE)
        event = scripts[0].text.splitlines()[-1]
        self.assertEqual(event.count("{"), 1)  # the position override the typesetter wrote
        self.assertNotIn("\\fs90", event)
        self.assertNotIn("\\N", event)

    @needs_downloads
    def test_files_are_written_for_ffmpeg(self):
        with tempfile.TemporaryDirectory() as directory:
            source, translated = os.path.join(directory, "a.srt"), os.path.join(directory, "b.srt")
            Path(source).write_text(srt(SAMPLES["en"][2]), encoding="utf-8")
            Path(translated).write_bytes(("\ufeff" + srt(SAMPLES["zh"][2])).encode("utf-8"))
            scripts, summary = typeset.typeset_files(source, translated, directory, *LANDSCAPE)
            self.assertEqual([script.name for script in scripts], ["secondary.ass", "main.ass"])
            for script in scripts:
                self.assertEqual(Path(directory, script.name).read_text(encoding="utf-8"), script.text)
            self.assertEqual(summary[MAIN]["font"], "Noto Sans SC Book")
            self.assertEqual(summary[SECONDARY]["cues"], 1)
            self.assertEqual(
                typeset.filter_chain(scripts, fonts_dir="fonts", directory="/work"),
                "ass=/work/secondary.ass:fontsdir=fonts:shaping=simple,ass=/work/main.ass:fontsdir=fonts:shaping=simple",
            )

    def test_paths_ffmpeg_would_misread_are_refused(self):
        script = [typeset.Script("main.ass", typeset.SIMPLE, "")]
        for directory in ("/tmp/it's here", "/tmp/a:b", "/tmp/a,b", "C:\\work", "/tmp/[x]", "/tmp/a b"):
            with self.assertRaises(ValueError, msg=directory):
                typeset.filter_chain(script, directory=directory)
        with self.assertRaises(ValueError):
            typeset.filter_chain(script, fonts_dir="/fonts dir", directory="/tmp")


class LineTests(unittest.TestCase):
    """Where a cue is broken."""

    def test_nothing_is_lost_in_any_frame_shape(self):
        for language, (script, style, ordinary, long) in AVAILABLE.items():
            for role in (MAIN, SECONDARY):
                track = track_for(role, ordinary, long)
                for size in (LANDSCAPE, PORTRAIT, SQUARE, FULL_HD):
                    for text in (ordinary, long):
                        with self.subTest(language=language, role=role, size=size):
                            block, _ = typeset_line(text, role, size, track)
                            tokens = [token for line in block.lines for token in line]
                            rebuilt = "".join(
                                (" " if index and token.space_before else "") + token.text
                                for index, token in enumerate(tokens)
                            )
                            self.assertEqual(rebuilt, typeset.clean_text(text))
                            self.assertTrue(all(block.lines))

    @needs_downloads
    def test_a_line_that_fits_stays_on_one_line(self):
        # The pair the look was designed for, at the lengths the worker splits to.
        for text, role in (
            ("旨在添加一门易学的脚本语言", MAIN),
            ("一" * 27, MAIN),
            ("with the goal of adding an easy-to-learn scripting language", SECONDARY),
            ("and that is why almost every website you have ever visited is running JavaScript", SECONDARY),
            ("and that is why almost every website you have ever visited is running JavaScript", MAIN),
        ):
            block, _ = typeset_line(text, role)
            self.assertEqual(len(block.lines), 1, text)
        # A little too long is tightened, not broken: by the tracking first, then by a few percent of width.
        block, _ = typeset_line("如今它运行在数十亿台设备上从网页浏览器到服务器再到智能手机", MAIN)
        self.assertEqual(len(block.lines), 1)
        spacing, scale = block.squeeze
        self.assertLess(spacing, 1.0)
        self.assertGreaterEqual(scale, typeset.MIN_SCALE_X[MAIN])

    @needs_downloads
    def test_a_broken_line_is_broken_into_even_rows(self):
        for language in ("zh", "zh-TW", "ja", "ko", "en", "de", "ru", "es"):
            for role in (MAIN, SECONDARY):
                with self.subTest(language=language, role=role):
                    block, _ = typeset_line(SAMPLES[language][3], role)
                    lines = line_texts(block)
                    self.assertIn(len(lines), (2, 3), lines)
                    # No row is left with a word or two; a break after a comma may cost some evenness.
                    lengths = sorted(len(line) for line in lines)
                    self.assertGreater(lengths[0] / lengths[-1], 0.5, lines)
        block, _ = typeset_line(SAMPLES["zh"][3], MAIN)
        self.assertEqual(len(block.lines), 2)

    @needs_downloads
    def test_words_names_and_numbers_are_never_cut(self):
        text = "这门语言叫做 JavaScript 由 Brendan Eich 在 1995 年设计出来 至今仍运行在 3,000,000,000 台设备上"
        for size in (LANDSCAPE, PORTRAIT, SQUARE, (360, 640)):
            for role in (MAIN, SECONDARY):
                lines = line_texts(typeset_line(text, role, size)[0])
                for whole in ("JavaScript", "Brendan", "Eich", "1995", "3,000,000,000"):
                    self.assertEqual(sum(whole in line for line in lines), 1, (size, whole, lines))
        for language in ("en", "de", "ru", "vi", "hi", "ar", "ko"):
            words = set(typeset.clean_text(SAMPLES[language][3]).split())
            for size in (LANDSCAPE, PORTRAIT):
                lines = line_texts(typeset_line(SAMPLES[language][3], MAIN, size)[0])
                self.assertEqual({word for line in lines for word in line.split()}, words, (language, size))

    @needs_downloads
    def test_punctuation_stays_with_its_word(self):
        closing, opening = "，。、！？；：）」』】》", "（「『【《"
        texts = (
            "他说：「这门语言（JavaScript）只用了十天就写好了」，然后大家都笑了，真的假的？当然是真的！",
            "彼は「この言語（JavaScript）は十日間で作られました」と言って、みんなが笑いました。本当ですか？本当です！",
        )
        for text in texts:
            for size in (LANDSCAPE, PORTRAIT, SQUARE, (360, 640), (300, 300)):
                for role in (MAIN, SECONDARY):
                    lines = line_texts(typeset_line(text, role, size)[0])
                    self.assertGreater(len(lines), 1)
                    for line in lines:
                        self.assertNotIn(line[0], closing, (size, lines))
                        self.assertNotIn(line[-1], opening, (size, lines))

    @needs_downloads
    def test_phrase_models_are_optional(self):
        def forget():
            typeset._PARSERS.clear()
            typeset._phrase_starts.cache_clear()

        japanese, chinese = SAMPLES["ja"][3], SAMPLES["zh"][3]
        with_models = [line_texts(typeset_line(text, MAIN, PORTRAIT)[0]) for text in (japanese, chinese)]
        self.addCleanup(forget)
        forget()
        with mock.patch.dict(sys.modules, {"budoux": None}):
            self.assertIsNone(typeset._phrase_parser("ja"))
            for text, modelled in zip((japanese, chinese), with_models):
                lines = line_texts(typeset_line(text, MAIN, PORTRAIT)[0])
                self.assertEqual("".join(lines).replace(" ", ""), typeset.clean_text(text).replace(" ", ""))
                self.assertLessEqual(abs(len(lines) - len(modelled)), 1)
        forget()
        self.assertIsNotNone(typeset._phrase_parser("ja"), "budoux is in requirements.txt")


class LayoutTests(unittest.TestCase):
    """Where the two rows are put."""

    def test_type_is_sized_from_the_short_side(self):
        landscape = typeset.geometry(*LANDSCAPE)
        self.assertAlmostEqual(landscape.unit, 480 / 288)
        self.assertAlmostEqual(landscape.bottom, 20 * 480 / 288)
        self.assertAlmostEqual(landscape.max_width, 854 * (1 - 20 / 384))
        self.assertEqual(landscape.centre, 427)
        # The same type on a phone screen as on a landscape frame of that width's height.
        portrait = typeset.geometry(*PORTRAIT)
        self.assertAlmostEqual(portrait.unit, 480 / 288)
        self.assertAlmostEqual(portrait.max_width, 480 * 0.91)
        self.assertAlmostEqual(portrait.bottom, 854 * 0.085)  # above the player's controls
        self.assertAlmostEqual(typeset.geometry(*SQUARE).unit, 480 / 288)
        self.assertAlmostEqual(typeset.geometry(*FULL_HD).unit, 1080 / 288)

    @needs_downloads
    def test_scripts_are_written_at_the_frame_size(self):
        for size in (LANDSCAPE, PORTRAIT, FULL_HD):
            scripts, summary = typeset.build_scripts(cues(SAMPLES["en"][2]), cues(SAMPLES["zh"][2]), *size)
            unit = typeset.geometry(*size).unit
            self.assertEqual((summary["width"], summary["height"]), size)
            for script, (family, points) in zip(scripts, (("VL Roboto Cond Sub", 18), ("Noto Sans SC Book", 23.7))):
                self.assertIn(f"PlayResX: {size[0]}\nPlayResY: {size[1]}\n", script.text)
                self.assertIn("WrapStyle: 2\n", script.text)  # libass must not break lines again
                style = re.search(r"^Style: Default,([^,]+),([\d.]+),", script.text, re.M)
                self.assertEqual(style.group(1), family)
                self.assertAlmostEqual(float(style.group(2)), points * unit, places=2)

    @needs_downloads
    def test_translation_sits_on_the_source_row(self):
        scripts, _ = typeset.build_scripts(cues(SAMPLES["en"][2]), cues(SAMPLES["zh"][2]), *LANDSCAPE)
        (_, source_y), = positions(scripts[0])
        (x, main_y), = positions(scripts[1])
        unit = 480 / 288
        self.assertEqual(x, 427)
        self.assertAlmostEqual(source_y, 480 - 20 * unit, places=1)
        self.assertAlmostEqual(main_y, 480 - 38 * unit, places=1)  # MarginV 20 and 38 of the plain filter

    @needs_downloads
    def test_a_two_line_source_lifts_only_its_own_translation(self):
        english, chinese = SAMPLES["en"], SAMPLES["zh"]
        scripts, summary = typeset.build_scripts(
            cues(english[2], english[3], english[2]), cues(chinese[2], chinese[2], chinese[2]), *LANDSCAPE
        )
        self.assertEqual(summary[SECONDARY]["two_lines"], 1)
        first, lifted, third = (y for _, y in positions(scripts[1]))
        self.assertEqual(first, third)
        one_row = 18 * 480 / 288
        self.assertGreater(first - lifted, one_row * 0.9)
        self.assertLess(first - lifted, one_row * 1.4)
        # The source row itself never moves.
        self.assertEqual(len({y for _, y in positions(scripts[0])}), 1)

    def test_each_cue_goes_to_the_shaper_its_script_needs(self):
        thai = SAMPLES["th"]
        scripts, summary = typeset.build_scripts(cues(SAMPLES["en"][2]), cues(thai[2], "OK 2024", thai[3]), *LANDSCAPE)
        self.assertEqual(
            [(script.name, script.shaping) for script in scripts],
            [("secondary.ass", "simple"), ("main.ass", "simple"), ("main_complex.ass", "complex")],
        )
        events = [script.text.count("\nDialogue:") for script in scripts]
        self.assertEqual(events, [1, 1, 2])
        self.assertEqual(summary[MAIN]["cues"], 3)
        self.assertEqual(summary[MAIN]["font"], "VL Noto Sans Thai")

    def test_right_to_left_lines_are_marked(self):
        for language in ("ar", "fa", "ur", "he"):
            scripts, _ = typeset.build_scripts([], cues(SAMPLES[language][3]), *LANDSCAPE)
            (script,) = scripts
            self.assertEqual(script.shaping, "complex")
            event = script.text.splitlines()[-1].split(",,", 1)[1]
            body = event.split("}", 1)[1]
            for line in body.split("\\N"):
                self.assertTrue(line.startswith(typeset.RLM), (language, line))

    @needs_downloads
    def test_empty_tracks_write_nothing(self):
        self.assertEqual(typeset.build_scripts([], [], *LANDSCAPE), ([], {"width": 854, "height": 480}))
        scripts, summary = typeset.build_scripts([], cues(SAMPLES["zh"][2]), *LANDSCAPE)
        self.assertEqual([script.name for script in scripts], ["main.ass"])
        self.assertNotIn(SECONDARY, summary)
        self.assertEqual(typeset.filter_chain([]), "")


def _ink(frame, width, height, threshold=96):
    """(left, right, top, bottom) of everything brighter than `threshold` in a grey frame, or None."""
    marks = frame.translate(bytes(1 if value > threshold else 0 for value in range(256)))
    left, right, top, bottom = width, -1, None, None
    for y in range(height):
        row = marks[y * width:(y + 1) * width]
        first = row.find(1)
        if first < 0:
            continue
        left, right = min(left, first), max(right, row.rfind(1))
        top, bottom = (y if top is None else top), y
    return None if top is None else (left, right, top, bottom)


def _ffmpeg_with_libass():
    """The ffmpeg the app burns with (the managed one once installed), None when it has no `ass` filter."""
    path = os.environ.get("PATH", "")
    try:
        from runtime_libraries import configure_ffmpeg

        configure_ffmpeg()  # offline: puts the managed ffmpeg first on PATH when it is there
    except Exception:
        pass
    ffmpeg = shutil.which("ffmpeg")
    os.environ["PATH"] = path
    if not ffmpeg:
        return None
    filters = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return ffmpeg if re.search(r"^\s*\S+\s+ass\s", filters, re.M) else None


class RenderTests(unittest.TestCase):
    """What ffmpeg and libass make of the scripts."""

    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = _ffmpeg_with_libass()
        if not cls.ffmpeg:
            raise unittest.SkipTest("needs an ffmpeg with libass (python installer.py installs one)")

    def _directory(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return directory.name

    def _draw(self, filters, size):
        """One black frame with `filters` drawn on it: (grey pixels, ffmpeg log)."""
        width, height = size
        completed = subprocess.run(
            [
                self.ffmpeg, "-hide_banner", "-nostdin",
                "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=1:d=1",
                "-vf", filters, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        log = completed.stderr.decode("utf-8", "replace")
        self.assertEqual(completed.returncode, 0, log[-2000:])
        self.assertEqual(len(completed.stdout), width * height)
        return completed.stdout, log

    def _draw_scripts(self, scripts, size):
        directory = self._directory()
        for script in scripts:
            Path(directory, script.name).write_text(script.text, encoding="utf-8")
        chain = typeset.filter_chain(scripts, fonts_dir=typeset.FONTS_DIR, directory=directory)
        return self._draw("format=yuv420p," + chain, size)

    def test_no_language_runs_off_the_frame(self):
        for size in (LANDSCAPE, PORTRAIT, SQUARE):
            width, height = size
            geom = typeset.geometry(width, height)
            side = (width - geom.max_width) / 2
            for language, (script, style, ordinary, long) in AVAILABLE.items():
                with self.subTest(language=language, size=size):
                    scripts, _ = typeset.build_scripts(cues(long), cues(long), width, height)
                    frame, log = self._draw_scripts(scripts, size)
                    self.assertNotIn("not found in font", log)
                    self.assertNotIn("failed to find any fallback", log)
                    ink = _ink(frame, width, height)
                    self.assertIsNotNone(ink, "nothing was drawn")
                    left, right, top, bottom = ink
                    self.assertGreaterEqual(left, side - 2)
                    self.assertLessEqual(right, width - side + 2)
                    self.assertLessEqual(bottom, height - geom.bottom + 2)
                    self.assertGreater(top, height * 0.05)

    @needs_downloads
    def test_libass_finds_every_face_by_the_name_written(self):
        samples = {}
        for language, (script, style, ordinary, long) in SAMPLES.items():
            for role in (MAIN, SECONDARY):
                samples.setdefault(track_for(role, ordinary, long).style.family, ordinary[:8])
        samples.setdefault("VL Roboto Cond Sub", "Привет")
        self.assertEqual(set(samples), set(typeset.FONT_FILES))
        families = sorted(samples)
        document = (
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 960\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            + "".join(
                f"Style: S{index},{family},24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
                "0,0,0,0,100,100,0,0,1,1,0,2,0,0,0,1\n"
                for index, family in enumerate(families)
            )
            + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            + "".join(
                f"Dialogue: 0,0:00:00.00,0:00:01.00,S{index},,0,0,0,,{samples[family]}\n"
                for index, family in enumerate(families)
            )
        )
        directory = self._directory()
        Path(directory, "faces.ass").write_text(document, encoding="utf-8")
        _, log = self._draw(
            f"ass={directory}/faces.ass:fontsdir={typeset.FONTS_DIR}:shaping=complex", (1280, 960)
        )
        self.assertNotIn("not found in font", log)
        for family in families:
            with self.subTest(family=family):
                chosen = re.search(r"fontselect: \(%s, 400, 0\) -> ([^\n]*)" % re.escape(family), log)
                self.assertIsNotNone(chosen, log[-3000:])
                self.assertNotIn(f"Using default font family: ({family},", log)
                # The face chosen is the one shipped for that name, by its PostScript name.
                squashed = re.sub(r"[^a-z0-9]", "", chosen.group(1).lower())
                self.assertIn(re.sub(r"[^a-z0-9]", "", family.lower()), squashed)


if __name__ == "__main__":
    unittest.main()
