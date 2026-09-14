# 原始音频提取质量与克隆参考音频（关联 #533）

范围有限：本改动只回升 3.0.0 重构时降低的三处音频参数，并给归一化加峰值保护。
它不解决 #533 报告的全部症状，也未做真实 TTS 听测。成片响度已由 #610 单独处理。

## 改了什么

| 位置 | 3.0.0 至 #610 | 本改动 |
| --- | --- | --- |
| `audio_preprocess.convert_video_to_audio` / `prepare_audio_for_asr` | `raw.mp3` 16 kHz / 32 kbps | 32 kHz / 128 kbps，`config.yaml` 的 `audio.raw_sample_rate` / `audio.raw_bitrate` 可覆盖；缺键回落默认；低于 16000 报错 |
| `audio_preprocess.normalize_audio_volume` | 目标 -20 dBFS，pydub 在 int16 上加增益，稀疏语音会削波 | 正增益封顶在峰值 -1 dBFS，衰减不受限；静音输入不再产生 `inf` |
| `sf_fishtts.merge_audio` | 合并参考导出 16 kHz | 44.1 kHz（`REFER_SAMPLE_RATE`），与切片源一致 |
| `config_utils.load_key_or` | 无 | 读取可选键，旧 `config.yaml` 无需改动 |

`aresample=async=1:first_pts=0` 与 PCM 回退保持不变（见 `docs/audio-timeline.md`）。

## 为什么

`raw.mp3` 不只是识别输入。WhisperX 内部固定 16 kHz，不受影响；但 Demucs 的人声、
`_9_refer_audio` 按字幕切出的 `refers/*.wav`、以及 `sf_fish_tts` custom/dynamic、`sf_cosyvoice2`、
`gpt_sovits`、`f5tts` 的克隆参考，全部继承提取时的带宽。

本机测量（ffmpeg 7.1，白噪声，48 kHz 源，8192 点 FFT，取相对 1 kHz 频段衰减 10 dB 处）：

| 提取参数 | -10 dB 截止 | 8 kHz 相对电平 | 体积 / 10 s |
| --- | --- | --- | --- |
| v2.2.1：32 kHz / 128 kbps | 约 15.3 kHz | 0 dB | 157 KB |
| 3.0.0 至 #610：16 kHz / 32 kbps | 约 7.2 kHz | -104 dB | 39 KB |
| 16 kHz 源再经 44.1 kHz / 128 kbps 重存（模拟 Demucs 输出） | 约 7.2 kHz | -87 dB | 157 KB |

3.0.0 降到 16 kHz 的原因是 302.ai WhisperX 云端 25 MB 上传限制，该服务已在 #609 移除；
ElevenLabs 路径按段解码到 16 kHz 再上传，与 `raw.mp3` 采样率无关。SiliconFlow 文档建议参考
音频用 192 kbps 以上 MP3 或 8 至 44.1 kHz WAV。

## 不覆盖什么

- 302.ai `fish_tts` 用固定 `reference_id`，不读本地参考，前两项对它没有影响；它的请求不带 `model`
  头，服务端默认模型随时间变化，本改动不处理。
- 「一句一句念」「句间不连贯」来自逐行合成、硬静音拼接与逐块 `atempo`，2.2.1 与 3.0 代码相同，本改动不动。
- 同一视频内句间响度差异不处理；成片整体响度由 #610 的门限响度归一化处理。
- 克隆音色是否因此变好，没有用真实 TTS 验证；能保证的只是可测的信号属性。

## 副作用

| 项目 | 变化 |
| --- | --- |
| `raw.mp3` 体积 | 每小时约 14 MB 变 58 MB；PCM 回退每小时约 115 MB 变 230 MB |
| `split_audio` 内存 | pydub 整段载入，翻倍：1 小时约 230 MB，3 小时约 690 MB |
| ASR | 识别仍在 16 kHz；转录缓存键不含提取参数，缓存继续命中 |
| Demucs | 运行时间不变，内部固定 44.1 kHz |
| SiliconFlow 上传 | 10 秒参考的 base64 约从 320 KB 增到 1.2 MB |
| 归一化 | 稀疏且峰值尖的人声轨，`vocal.mp3` 可能低于 -20 dBFS |

已有项目不会重新提取：`convert_video_to_audio` 见到 `output/audio/raw.mp3` 就跳过。要让改动生效，
需删除 `output/audio/` 下的 `raw.mp3`、`vocal.mp3`、`background.mp3`、`refers/`、`tmp/`、`segs/`，
或整个 `output/`；用 `sf_fish_tts` custom 模式还要把 `sf_fish_tts.custom_name` 置空以重建音色。

## 验证

```sh
python -m pytest -q tests/test_audio_extract_quality.py tests/test_audio_timeline.py
```

用例覆盖：提取命令参数（含旧配置缺键、PCM 回退）、真实 FFmpeg 的 9 至 14 kHz 频段保留断言、
归一化峰值上限与静音输入、参考合并采样率、`load_key_or` 回落、`config.yaml` 默认值。
未覆盖：真实 Demucs、真实 TTS 与克隆 API、听感、内存与耗时。
