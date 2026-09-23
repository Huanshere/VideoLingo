# Experimental ASR: AssemblyAI Universal-3.5 Pro via OpenRouter

Step 2 (`core/_2_asr.py`) can use OpenRouter's Sync transcription API instead of
local WhisperX or ElevenLabs. This path is experimental.

## Why chunking is required

OpenRouter serves `assemblyai/universal-3-5-pro` through Sync transcription:

- Endpoint: `POST https://openrouter.ai/api/v1/audio/transcriptions`
- Input: 16-bit WAV as base64 in `input_audio: { data, format: "wav" }`
- **Maximum ~120 seconds per request**

A 10-minute YouTube video cannot be sent in one call. VideoLingo converts the
requested interval to 16-bit mono WAV with ffmpeg (`audio_slice_wav`), splits it
into ~110s windows (small overlap, silence snap when possible), calls Sync per
chunk, then stitches text and word timestamps onto the original timeline.

## Config keys

```yaml
api:
  key: 'sk-or-...'                      # or export OPENROUTER_API_KEY
  base_url: 'https://openrouter.ai/api/v1'
  model: 'deepseek/deepseek-v4.1-flash' # LLM used after ASR (summarize/translate)

whisper:
  runtime: 'assemblyai'                 # local | elevenlabs | assemblyai
  language: 'en'                        # or auto
  assemblyai_model: 'assemblyai/universal-3-5-pro'
  openrouter_base_url: 'https://openrouter.ai/api/v1'
  openrouter_api_key: ''                # optional; falls back to OPENROUTER_API_KEY, then api.key
```

Auth is `Authorization: Bearer <key>`. The backend reads, in order:

1. `whisper.openrouter_api_key`
2. environment variable `OPENROUTER_API_KEY`
3. `api.key`

Downstream LLM steps already use `api.base_url` + `api.model`. Setting
`deepseek/deepseek-v4.1-flash` there is enough; this change does not add a
separate LLM client.

## Mac smoke test (~10 minute YouTube video)

```bash
brew install ffmpeg yt-dlp
export OPENROUTER_API_KEY='sk-or-...'

# config.yaml: whisper.runtime: assemblyai
#              api.base_url: https://openrouter.ai/api/v1
#              api.model: deepseek/deepseek-v4.1-flash
#              api.key: same key, or leave a placeholder if the env var is set

mkdir -p output
yt-dlp -f 'bv*+ba/b' --merge-output-format mp4 -o 'output/sample.%(ext)s' 'YOUTUBE_URL'

# Streamlit: select AssemblyAI (OpenRouter) and run subtitle processing
# or only step 2:
python -c 'from core import _2_asr; _2_asr.transcribe()'
```

Check `output/log/cleaned_chunks.xlsx`. Word `start`/`end` values should cover
the full clip, not only the first two minutes.

Unit tests mock HTTP and do not need a key:

```bash
python -m pytest tests/test_assemblyai_openrouter.py tests/test_asr_runtime.py -q
```
