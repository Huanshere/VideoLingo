## Magic Introduction 🪄✨

🔙 Back to README | [English](../README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) |  [Türkçe](README.tr.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

Welcome to SubMagic! The main features of this project can be summarized as follows:

1. **Video Download**: Use `yt-dlp` to download videos from specified URLs.
   - `core/step1_ytdlp.py`: Call the `download_video_ytdlp` function, passing in the video URL and save path to download the video file.

2. **Transcription**: Use OpenAI's `whisper` model to transcribe audio from the video into text.
   - `core/step2_whisper_stamped.py`: Call the `transcript` function, set language and timestamp return method, and save the transcription result as an Excel file.

3. **Text Processing**: Process the transcribed text, splitting sentences by punctuation and semantics.
   - `core/step3_1_spacy_split.py`: Use SpaCy model to split text, including splitting by comma (`split_by_comma_main`), period (`split_sentences_main`), and punctuation (`split_by_mark`).
   - `core/step3_2_splitbymeaning.py`: Call the `split_sentences_by_meaning` function, using the GPT model to split sentences based on semantics.

4. **Summarization**: Use the GPT model to summarize content and identify key terms.
   - `core/step4_1_summarize.py`: Call the `get_summary` function to generate content summaries and key terms.

5. **Translation**: Translate the processed text into another language, considering the identified key terms.
   - `core/step4_2_translate_all.py`: Call the `translate_all` function to divide the text into chunks and translate them.
   - `core/step4_2_translate_once.py`: Define the `translate_lines` function, using a three-step translation method (literal translation, free translation, and polishing) to translate English text line by line into the target language.

6. **Subtitle Alignment**: Align the translated text with the original transcription to generate subtitles.
   - `core/step5_splitforsub.py`: Call the `split_for_sub_main` function to split and adjust subtitle files, using the GPT model for subtitle alignment.

7. **Final Subtitle Generation**: Generate the final subtitles in SRT format, ensuring correct timing and alignment.
   - `core/step6_generate_final_timeline.py`: Call the `align_timestamp_main` function to generate the final subtitle timeline and output the subtitles in SRT format.
   - `core/step7_merge_sub_to_vid.py`: Call the `merge_subtitles_to_video` function to merge the generated subtitle file with the original video.

# 🧙‍♂️ SubMagic Q&A Magic Time 🎩✨

### Q: How to make the GPT model more "budget-friendly"? 💰
A: We're already using the super cost-effective deepseek-coder! It costs less than a dollar per video. Want to save even more? Try other models in `config.py` or optimize the subtitle splitting strategy. Don't forget to feed GPT well, it can't cast good spells on an empty stomach! 🍽️

### Q: Translation quality not magical enough? What to do? 🌈
A: Our three-step translation method is already pretty awesome! Want to take it to the next level? You can tweak the prompts in `prompts_storage.py` or switch to an even more powerful model. Let's make translation as magical as it can be! 🎭

### Q: Can SubMagic conjure up new tricks? 🌺
A: Of course! SubMagic is like a treasure chest, you can add any magical ingredients you want. The modular design allows you to easily add new features and customize the processing flow. Let your creativity run wild! 🛠️

### Q: Can the subtitle style be cooler? 😎
A: You can give subtitles a new look in `step7`! However, we recommend using professional software to give SubMagic-generated subtitles a magical makeover. Make them shine in your videos! ✨👗

### Q: The project's not running fast enough? I'm dying here! 🐢➡️🐇
A: Don't panic, we're already using multi-threading magic! Want to go even faster? Try simplifying the CoT steps in the prompts. Let's make SubMagic fly! 🚀

### Q: Subtitle splitting and alignment not smart enough? 🧠
A: We're currently using strategies based on character count, semantics, and timestamps. Want it smarter? You can adjust parameters based on language characteristics and reading speed, or try advanced algorithms like dynamic programming or machine learning. Let's make subtitle alignment as precise as magic! 🎯

### Q: There's "dirt" in the transcribed text, what to do? 🧹
A: No worries! Before feeding it to GPT, you can use regex or string processing for a big cleanup. Clean up punctuation, special characters, capitalization, etc. Give the text a purification ritual, make it brand new! 🧼✨