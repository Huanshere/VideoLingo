<div align="center">

<img src="/docs/logo.png" alt="شعار VideoLingo" height="140">

<div dir="rtl">

# نربط العالم، إطارًا بإطار

</div>

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)｜[**العربية**](/translations/README.ar.md)

</div>

<div dir="rtl">

## 🌟 نظرة عامة ([جرّب VL الآن!](https://videolingo.io))

يجمع VideoLingo بين التعرف على الكلام وترجمة الترجمات النصية وتقسيمها والدبلجة في واجهة Streamlit. وهو ينتج ملفات الترجمة النصية، ويمكنه اختياريًا إنتاج فيديوهات مترجمة نصيًا أو مدبلجة. تعتمد جودة الترجمة على الصوت المصدر واللغة والنماذج المختارة.

أبرز الميزات:
- 🎥 تنزيل فيديوهات YouTube عبر yt-dlp

- التعرف على الكلام ومحاذاته على مستوى الكلمة باستخدام Qwen3-ASR + Qwen3-ForcedAligner

- **📝 تقسيم الترجمة النصية بمعالجة اللغة الطبيعية (NLP) والذكاء الاصطناعي**

- **📚 مصطلحات مخصصة + مولَّدة بالذكاء الاصطناعي لترجمة متسقة**

- ترجمة مباشرة مع مراجعة ذاتية اختيارية وإعادة صياغة طبيعية

- تقسيم الترجمة النصية بحدود طول قابلة للضبط

- **🗣️ الدبلجة باستخدام GPT-SoVITS وOpenAI وEdge TTS وغيرها**

- 🚀 تشغيل ومعالجة بنقرة واحدة في Streamlit

- 🌍 دعم لغات متعددة في واجهة Streamlit

- 📝 سجلات مفصلة مع إمكانية استئناف التقدم

- 🔍 مربع بحث عن النماذج مع جلب تلقائي عبر API — ابحث ورشِّح من القائمة الكاملة للنماذج لدى مزوّدك

- ⏯️ التحكم في المهام — أوقف المعالجة مؤقتًا أو استأنفها أو أوقفها نهائيًا في أي خطوة

يجمع سير العمل بين النسخ الصوتي والترجمة وتنسيق الترجمة النصية والدبلجة في مشروع واحد.

## 🎥 عرض توضيحي

</div>

<table>
<tr>
<td width="33%">

<div dir="rtl">

### ترجمة نصية مزدوجة

</div>

---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

<div dir="rtl">

### استنساخ الصوت باستخدام Cosy2

</div>

---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

<div dir="rtl">

### GPT-SoVITS بصوتي

</div>

---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

<div dir="rtl">

### دعم اللغات

**لغات الإدخال:**

🇺🇸 الإنجليزية 🤩 | 🇷🇺 الروسية 😊 | 🇫🇷 الفرنسية 🤩 | 🇩🇪 الألمانية 🤩 | 🇮🇹 الإيطالية 🤩 | 🇪🇸 الإسبانية 🤩 | 🇯🇵 اليابانية 😊 | 🇨🇳 الصينية 🤩

تعتمد لغات الدبلجة على طريقة TTS المختارة.

## التثبيت

يدعم VideoLingo أنظمة Windows وmacOS (Apple Silicon / Intel) وLinux.

### اطلب من وكيل الذكاء الاصطناعي المحلي لديك 🤖

إذا كنت تستخدم وكيل ذكاء اصطناعي قادرًا على التحكم في جهازك، فأرسل إليه هذا الموجّه (prompt):

</div>

> Install and launch GitHub's Huanshere/VideoLingo on my computer.

<div dir="rtl">

### Windows: تثبيت بنقرة واحدة 🎉

1. نزّل **Source code (zip)** من [أحدث إصدار](https://github.com/Huanshere/VideoLingo/releases/latest)، وفكّ ضغطه على سطح المكتب أو في أي مجلد آخر، ثم افتح المجلد.
2. انقر نقرًا مزدوجًا على `OneKeyStart.bat` وأبقِ النافذة مفتوحة. في التشغيل الأول يثبّت تلقائيًا uv وPython 3.12 واعتماديات التطبيق وFFmpeg. يلزم اتصال بالإنترنت.
3. بعد انتهاء التثبيت يُفتح VideoLingo تلقائيًا في متصفحك. أدخل عنوان API والمفتاح والنموذج في الشريط الجانبي لتبدأ الاستخدام.

### التثبيت من المصدر (Windows وmacOS وLinux)

</div>

```bash
git clone https://github.com/Huanshere/VideoLingo.git && cd VideoLingo
uv run start.py
```

<div dir="rtl">

لتشغيله لاحقًا، نفّذ `uv run start.py` مرة أخرى من مجلد VideoLingo. يعتمد Apple Silicon على MLX، بينما تستخدم أجهزة Mac بمعالج Intel وحدة المعالجة المركزية (CPU) في التعرف على الكلام. وافتراضيًا، تستخدم الدبلجة على أجهزة Mac بمعالج Intel الصوت الجديد دون الصوت الخلفي الأصلي.

#### Docker (اختياري)

لنشر حاوية NVIDIA على Linux، ثبّت Docker وتعريف وحدة معالجة رسومية (GPU) متوافقًا و[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). تستخدم الصورة إعداد Python 3.12 نفسه واعتماديات التطبيق نفسها، مع CUDA 12.8.1/cu128 افتراضيًا. راجع [وثائق Docker](/docs/pages/docs/docker.en-US.md) للاطلاع على بديل CUDA 12.6 المقابل وإعدادات الحفظ الدائم للبيانات.

</div>

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

<div dir="rtl">

## HTTP API (يحل محل وضع Excel الدفعي)

للوكلاء والسكربتات، استخدم واجهة HTTP API المحلية بدلًا من وضع Excel الدفعي السابق.
تشارك هذه الواجهة خط المعالجة نفسه المستخدم في Streamlit وتعالج عملية واحدة في كل مرة باستخدام `output/`.
اضبط `config.yaml` وشغّلها من جذر المشروع. ويثبّت الأمر أيضًا الاعتماديات الناقصة عند أول استخدام:

</div>

```bash
uv run start.py --api
```

<div dir="rtl">

راجع **[دليل HTTP API](../docs/api.md)** للاطلاع على الإدخال والمعالجة والتقدم والتنزيلات
وإعادة المحاولة والمعالجة الدفعية المتسلسلة. وثائق نقاط النهاية التفاعلية: [localhost:8000/docs](http://localhost:8000/docs).

## مزوّدو LLM وASR وTTS
يدعم VideoLingo صيغة API المشابهة لـ OpenAI وعدة واجهات TTS:
- LLM: اختر مزوّدًا متوافقًا مع OpenAI Chat Completions ونموذجًا قادرًا على إرجاع JSON المنظَّم الذي يتطلبه سير العمل. يُوصى بـ[OpenLux](https://www.openlux.ai/register?aff=wKYu)؛ اضبط عنوان API على `https://api.openlux.ai/v1`. فضّل GPT-6 Luna بمعرّف النموذج `gpt-6-luna` لأفضل قيمة مقابل السعر، أو GPT-6 Sol بالمعرّف `gpt-6-sol` لجودة أفضل، أو Claude Opus 5.5 بالمعرّف `claude-opus-5-5` لأعلى جودة. تجد أسعار الوسيط (relay) في OpenLux في وثائق التثبيت. اضبط عنوان API والمفتاح والنموذج في الشريط الجانبي.
- التعرف على الكلام: شغّل Qwen3-ASR + ForcedAligner محليًا (الافتراضي)، أو اختر ElevenLabs أو MAI-Transcribe-2 من الشريط الجانبي. يدعم MAI مفتاح Azure Speech أو مفتاح OpenRouter يُدخل في الشريط الجانبي؛ ويُرسل الصوت إلى المزوّد المختار وقد تترتب على ذلك رسوم. لا يثبّت المثبّت WhisperX؛ ولاستخدامه كمحرّك للتعرف على الكلام، اتبع [WhisperX (تثبيت يدوي)](../docs/pages/docs/whisperx-manual.en-US.md).
- TTS: OpenAI وFish Audio وSiliconFlow Fish/CosyVoice2 وGPT-SoVITS وEdge TTS وF5-TTS ومحوّل مخصص في `core/tts_backend/custom_tts.py`.

للاطلاع على تعليمات التثبيت التفصيلية وإعداد LLM وطريقة الاستخدام، راجع الوثائق: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## القيود الحالية

1. تؤثر الضوضاء الخلفية ونماذج المحاذاة الخاصة بكل لغة في دقة التعرف على الكلام والطوابع الزمنية للكلمات. وقد يساعد فصل الصوت البشري عن بقية الأصوات. وقد لا تتوفر للأرقام والرموز أوقات موثوقة على مستوى الكلمة؛ لذا افحص ملفات الترجمة النصية الناتجة.

2. يجب أن يلتزم ناتج LLM ببنية JSON التي يتطلبها سير العمل. وعند حدوث أعطال، افحص `output/gpt_log/error.json`. يمكن إعادة استخدام ذاكرة التخزين المؤقت للاستجابات الناجحة والمخرجات المكتملة عند إعادة المحاولة؛ وتغيير النموذج وحده لا يعيد توليد كل المراحل المكتملة. لا تحذف كل محتويات مجلد output كأول خطوة لاستكشاف الأخطاء.

3. تعتمد جودة الدبلجة وتوقيتها على الترجمة وخدمة TTS وسرعة الكلام. ولا يضمن ضبط السرعة أداءً طبيعيًا ولا تزامنًا مثاليًا.

4. يستخدم التعرف المحلي لغة تعرف ومحاذاة رئيسية واحدة لكل مقطع صوتي. ولا يُضمن أن يحافظ الكلام المختلط بين لغات متعددة على نص وتوقيت دقيقين في كل لغة.

5. لا يخصص سير عمل الدبلجة تلقائيًا صوتًا منفصلًا لكل متحدث.

## 📄 الترخيص

هذا المشروع مرخَّص بموجب ترخيص Apache 2.0. شكر خاص لمشاريع المصدر المفتوح التالية على إسهاماتها:

</div>

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

<div dir="rtl">

## 📬 تواصل معي

- قدّم [المشكلات (Issues)](https://github.com/Huanshere/VideoLingo/issues) أو [طلبات الدمج (Pull Requests)](https://github.com/Huanshere/VideoLingo/pulls) على GitHub
- راسلني على Twitter: [@Huanshere](https://twitter.com/Huanshere)
- راسلني عبر البريد الإلكتروني: team@videolingo.io

## ⭐ سجل النجوم

</div>

[![مخطط سجل النجوم](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">إذا وجدت VideoLingo مفيدًا، فمن فضلك امنحني ⭐️!</p>

ترجمة: فريق مُشَيِّد
