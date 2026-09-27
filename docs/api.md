# Local HTTP API / 本地 API

The API replaces Excel batch mode. It uses the **same pipeline as Streamlit**, the existing
`config.yaml`, fixed `output/`, and `history/`. There is one operation at a time, no queue,
no database and no task directories. Use either the UI or API for a working directory.

API 替代原来的 Excel 批处理入口，与 Streamlit 共用流程。保留 `config.yaml`、`output/`
和 `history/`。一次只执行一个操作；多个视频由调用方逐个提交，不需要队列或任务目录。
同一工作目录选择 UI 或 API 一种方式使用。

## Start

Install the project dependencies as usual (`python installer.py`), configure your LLM
and other settings in `config.yaml`, then run from the repository root:

```bash
python api.py
```

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

已有中间文件会被复用。修改语言或模型后如需重做，请明确归档或替换旧输出；不会自动推断
缓存失效。停止是协作式的，请等 `active: false` 后再开始下一项。

## Tests (no model downloads)

```bash
python -m pip install pytest httpx
python -m pytest tests/test_api.py
```
