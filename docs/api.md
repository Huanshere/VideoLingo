# Local HTTP API

The API replaces Excel batch mode. It uses the **same pipeline as Streamlit**, the existing
`config.yaml`, fixed `output/`, and `history/`. There is one operation at a time, no queue,
no database and no task directories. Use either the UI or API for a working directory.

## Start

Configure your LLM and other settings in `config.yaml`, then run from the repository root.
The same command installs any missing dependencies on first use:

```bash
uv run start.py --api
```

If you used the Windows one-click installer, run `.\OneKeyStart.bat --api` instead;
it uses the same environment as the double-click launcher.

The server listens on `127.0.0.1:8000`. Interactive documentation: http://127.0.0.1:8000/docs;
OpenAPI schema: http://127.0.0.1:8000/openapi.json. This is a trusted local API with no
authentication; keep it on localhost. Run one server process, without multiple workers.

## Process a video

Send JSON with `Content-Type: application/json`:

```http
POST /input
{"source": "/absolute/path/video.mp4"}
```

On Windows use a JSON path such as `"C:/Videos/video.mp4"`. HTTP(S) video URLs are also
accepted. Local files are copied into `output/`; source files are untouched.
`202` means accepted, not finished. Poll `GET /status` until `active` is false and
`state` is `completed`, then start processing:

```http
POST /run
{"stage": "all", "target_language": "zh", "dubbing": true}
```

`stage` is `subtitles`, `dubbing`, or `all` (default). `dubbing` defaults to false and
only controls whether `all` includes dubbing. `stage: dubbing` requires existing subtitles.
On Intel Macs, dubbing uses the new voice without mixing in the original background sound.
Audio-only input supports subtitles, matching the UI. Optional `source_language` and
`target_language` are saved to `config.yaml`; other settings use that file directly.
Do not edit configuration while processing.

Poll `GET /status` again. It returns `state`, `active`, `step`, `step_index` (zero-based),
`total_steps`, `progress`, `error`, and top-level output `files`. Progress counts completed
step groups, not elapsed time. States: `idle`, `running`, `paused`, `stopping`, `stopped`,
`completed`, `error` (`paused` is used by the shared UI runner).

```http
GET /files/trans.srt
POST /archive
```

Output files are also available directly in `output/`. File downloads only serve top-level
files inside this directory. `/archive` runs in the background: wait for completion before
preparing the next video. It retains the existing history behavior (same-name archives may
be overwritten); move results elsewhere first if you want to keep multiple versions.

## Serial processing, retries and stopping

- A busy `/input`, `/run`, or `/archive` returns `409`. Wait before submitting the next operation.
- `/input` rejects nonempty `output/` by default. Explicitly pass `"existing": "archive"`
  or `"existing": "replace"` to archive or delete old output before preparing the next input.
- Failed operations expose the error and step through `/status`. Fix the cause, then repeat
  `/run` to reuse existing intermediate files. No automatic whole-step retry is added.
- Changing parameters does **not** invalidate intermediate files. To regenerate with different
  settings, prepare the source again with `existing: archive` or `replace`, then run.
- `POST /stop` requests cooperative cancellation. It may wait for the current model/network call
  to finish. Wait for `active: false` before retrying or replacing input.
- Status is in memory. After a server restart it is `idle`; files remain, and `/run` can retry.
- No CLI, Excel task file, persistent job history, or service queue is needed. An agent can loop:
  input → wait → run → wait → collect results → archive → wait → next input.

## Tests (no model downloads)

These commands use the project `.venv`. If you use a shared environment, replace `.venv`
with its path in both commands.

```bash
uv pip install --python .venv pytest httpx
uv run --python .venv pytest tests/test_api.py
```
