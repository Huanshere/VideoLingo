# Task Workspace Design

## Goal

Move VideoLingo from a single shared `output/` workflow toward isolated task workspaces. The first version should protect users from cross-run file/config pollution while preserving the current pipeline behavior.

This is the foundation for later review pages, resumable retries, cost tracking, and provider health checks.

## Current Problem

The app writes most intermediate and final artifacts into global paths such as `output/`, `history/`, and `batch/output/`. Batch processing also temporarily mutates global `config.yaml` values. This makes it easy for one video run to affect another run, especially when users retry failed work, process multiple videos, or switch language/API settings.

## Recommended Approach

Use a lightweight workspace layer before adding a database.

Each task gets a directory under:

```text
workspace/jobs/<job_id>/
```

Initial layout:

```text
workspace/jobs/<job_id>/
  job.yaml
  config.snapshot.yaml
  output/
  logs/
  artifacts/
```

`job.yaml` stores task metadata and status. `config.snapshot.yaml` stores the effective config at task creation time. `output/` mirrors the current global `output/` layout so the existing pipeline can be migrated gradually.

## Scope For Version 1

Version 1 includes:

- Create a new workspace for each Streamlit task.
- Continue an existing workspace from the UI.
- Archive a workspace without deleting it.
- Save a config snapshot per workspace.
- Route pipeline output paths through a small path helper instead of hardcoding new global paths.
- Keep compatibility with the existing `output/` directory during migration.
- Update batch mode so each video receives its own workspace and config snapshot.

Version 1 does not include:

- SQLite or a full task database.
- Multi-user permissions.
- Concurrent execution of multiple tasks in one Streamlit session.
- Human subtitle/terminology/translation review pages.
- Cost estimation and provider health dashboards.

Those features should build on top of this workspace layer later.

## Data Model

`job.yaml`:

```yaml
id: "20260503-153012-video-title"
name: "Video title"
source:
  type: "upload|youtube|batch"
  path: ""
  url: ""
status: "created|running|paused|completed|failed|archived"
created_at: "2026-05-03T15:30:12+08:00"
updated_at: "2026-05-03T15:30:12+08:00"
current_stage: ""
error: ""
```

The schema is intentionally small. Later versions can add review checkpoints, token/cost totals, provider health, and retry history without changing the core directory layout.

## Path Strategy

Add a `core/workspace.py` module that owns:

- Creating job IDs and directories.
- Reading/writing `job.yaml`.
- Saving config snapshots.
- Resolving paths such as `output/log/cleaned_chunks.xlsx` relative to the active workspace.
- Falling back to the legacy project root for old runs.

Existing modules should avoid constructing fresh `output/...` strings when touched. The first migration target is `core/utils/models.py`, because many pipeline files import output constants from there.

## Streamlit UX

The first screen should become a simple task selector:

- New task
- Continue task
- Archive task

When a task is active, the app shows the current workspace name and status. Existing download buttons and preview behavior should continue to work because they read from the active workspace output directory.

The UI should avoid exposing internal paths unless useful for debugging.

## Batch UX

Batch mode should create one workspace per input video. Each workspace receives:

- The per-row source/target language values.
- A config snapshot.
- Its own output directory.
- Its own status and error message.

Batch progress can still be written back to `batch/tasks_setting.xlsx`, but the workspace path should be stored so failed tasks can resume from the correct files.

## Error Handling

If a workspace cannot be created or loaded, the app should fail before starting the pipeline.

If a task fails during processing, the active workspace remains intact and `job.yaml` records the failed stage and error message. Users can retry using the same workspace.

If no active workspace exists, path helpers should default to legacy behavior so older scripts remain usable.

## Testing

Add focused tests for:

- Creating a workspace and writing metadata.
- Saving config snapshots without mutating global config.
- Resolving output paths with and without an active workspace.
- Batch workspace creation per video row.
- Legacy fallback to `output/`.

Manual verification:

- Start a new Streamlit task and confirm files land under `workspace/jobs/<job_id>/output/`.
- Start a second task and confirm it does not read the first task's output.
- Run batch mode with two videos and confirm each receives separate workspace files.

## Implementation Notes

This should be done incrementally:

1. Add workspace module and tests.
2. Add active workspace selection in Streamlit session state.
3. Migrate output constants in `core/utils/models.py`.
4. Update cleanup/download/history paths to use active workspace paths.
5. Update batch mode to create and use per-video workspaces.

The migration should keep old `output/` behavior working until all pipeline modules have moved to workspace-aware paths.
