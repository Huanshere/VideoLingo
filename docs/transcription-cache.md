# Persistent transcription cache

ASR results are cached under `.cache/asr/`, outside `output/` and `history/`.
Reuploading an identical media file reuses recognition even after the working output
has been cleared. Renaming a file does not change its identity. Successful segments
are saved individually so a failed later segment can be retried without repeating
earlier recognition. A complete hit skips recognition model loading. Audio preparation
is retained because later alignment and dubbing stages still require those files.

Identity includes the source file MD5, recognition language, runtime, model setting,
vocal separation, installed ASR package versions and a cache schema version. The
source bytes are hashed, not only the filename or duration. A re-encode is a miss,
even if it sounds identical. Credentials and translation settings are not stored.
Cached results contain transcript text and timestamps: keep this local directory
private. It is already ignored by Git.

Language metadata is restored on every hit. Failed requests, cancellation and
incomplete JSON writes are not reused. Legacy cloud logs named only by time range
are not trusted as cache entries because they do not identify their source media.
Existing `cleaned_chunks.xlsx` retains the normal in-progress step-skipping behavior.
Old archives are not automatically imported into the new cache.

To bypass persistent caching, add `cache: false` under `whisper` in config.yaml.
To reclaim disk space or force rebuilding after changing a custom model in-place,
remove `.cache/asr/` while no task is running. No automatic eviction is performed.
Remote providers can change a model behind the same name: bypass/clear the cache
when a fresh provider result is required. No translation or TTS result caching is
added here; existing LLM response caching is independent.
