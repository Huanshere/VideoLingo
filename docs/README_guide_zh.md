## 魔法简介 🪄✨

🔙 回到 README | [English](../README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) |  [Türkçe](README.tr.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

欢迎来到 SubMagic ！这个项目的主要功能可以总结如下：

1. **视频下载**：使用 `yt-dlp` 从指定的 URL 下载视频。
   - `core/step1_ytdlp.py`：调用 `download_video_ytdlp` 函数，传入视频 URL 和保存路径，下载视频文件。

2. **转录**：使用 OpenAI 的 `whisper` 模型将视频中的音频转录为文本。
   - `core/step2_whisper_stamped.py`：调用 `transcript` 函数，设置语言和时间戳返回方式，将转录结果保存为 Excel 文件。

3. **文本处理**：对转录的文本进行处理，按标点符号和语义分割句子。
   - `core/step3_1_spacy_split.py`：使用 SpaCy 模型对文本进行分割，包括按逗号 (`split_by_comma_main`)、句号 (`split_sentences_main`) 和标点符号 (`split_by_mark`) 分割。
   - `core/step3_2_splitbymeaning.py`：调用 `split_sentences_by_meaning` 函数，使用 GPT 模型根据语义对句子进行分割。

4. **总结**：使用 GPT 模型对内容进行总结，并识别关键术语。
   - `core/step4_1_summarize.py`：调用 `get_summary` 函数，生成内容总结和关键术语。

5. **翻译**：将处理后的文本翻译成另一种语言，并考虑识别出的关键术语。
   - `core/step4_2_translate_all.py`：调用 `translate_all` 函数，将文本分块并进行翻译。
   - `core/step4_2_translate_once.py`：定义 `translate_lines` 函数，使用三步翻译法（直译、意译和润色）将英文文本逐行翻译成目标语言。

6. **字幕对齐**：将翻译后的文本与原始转录对齐，生成字幕。
   - `core/step5_splitforsub.py`：调用 `split_for_sub_main` 函数，对字幕文件进行分割和调整，使用 GPT 模型进行字幕对齐。

7. **最终字幕生成**：生成 SRT 格式的最终字幕，确保时间和对齐正确。
   - `core/step6_generate_final_timeline.py`：调用 `align_timestamp_main` 函数，生成最终的字幕时间轴，并输出 SRT 格式的字幕文件。
   - `core/step7_merge_sub_to_vid.py`：调用 `merge_subtitles_to_video` 函数，将生成的字幕文件合并到原视频中。

# 🧙‍♂️ SubMagic 魔法问答时间 🎩✨

### Q: 如何让 GPT 模型更"经济实惠"? 💰
A: 已经用上超级划算的 deepseek-coder 啦!一个视频才花不到1块钱。想再省?试试 `config.py` 里的其他模型,或者优化字幕分割策略。别忘了给 GPT 喂饱饱,饿着肚子可施不出好魔法! 🍽️

### Q: 翻译质量不够魔幻?该咋办? 🌈
A: 我们的三步翻译法已经很厉害啦!还想更上一层楼?可以在 `prompts_storage.py` 里调教一下提示词,或者换个更厉害的模型。让翻译变得如魔法般神奇! 🎭

### Q: SubMagic 能变出新花样吗? 🌺
A: 当然!SubMagic 就是个百宝箱,想加什么魔法材料都行。模块化设计让你可以轻松添加新功能,自定义处理流程。快来发挥你的创意吧! 🛠️

### Q: 字幕样式能不能更酷炫? 😎
A: `step7` 里可以给字幕穿新衣服哦!不过,更推荐用专业软件给 SubMagic 生成的字幕来个魔法变身。让它们在视频里闪闪发光! ✨👗

### Q: 项目跑得不够快?急死我啦! 🐢➡️🐇
A: 别急别急,我们已经用上多线程魔法啦!想再快点?试试简化 prompt 的 CoT 步骤。让 SubMagic 飞起来! 🚀

### Q: 字幕分块和对齐还不够智能? 🧠
A: 目前用的是基于字符数、语义和时间戳的策略。想更智能?可以根据语言特点、阅读速度来调整参数,或者尝试高级算法如动态规划、机器学习。让字幕对齐变得精准如魔法! 🎯

### Q: 转录文本里有"脏东西",咋办? 🧹
A: 别担心!在喂给 GPT 之前,可以用正则表达式或字符串处理来个大扫除。清理标点、特殊字符、大小写等。给文本来个净化仪式,焕然一新! 🧼✨