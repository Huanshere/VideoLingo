# Human Review Workbench Design

## Goal

Add a human confirmation page for terminology, translation, subtitle segmentation, and TTS text inside each VideoLingo task workspace.

The first version should turn the pipeline from a black-box run into a controllable review workflow without replacing the existing JSON, Excel, and SRT artifacts. The feature should help long-video users catch terminology mistakes, awkward translations, bad subtitle splits, and unnatural TTS text before final video generation.

## Current Problem

VideoLingo already generates useful intermediate files:

- `output/log/terminology.json`
- `output/log/translation_results.xlsx`
- `output/log/translation_results_for_subtitles.xlsx`
- `output/log/translation_results_remerged.xlsx`
- `output/audio/tts_tasks.xlsx`
- final SRT files under `output/` and `output/audio/`

However, the Streamlit flow currently runs major stages in sequence. Users can edit files manually, but the product does not tell them when to review, what file matters, or which later steps must be rerun after a correction.

This is especially painful for long videos because one terminology mistake can propagate into many lines, and one bad subtitle split can affect both display subtitles and dubbing.

## Recommended Approach

Add a lightweight review workbench inside the active task workspace.

The workbench exposes four review tabs:

1. Terminology
2. Translation
3. Subtitles
4. TTS Text

Each tab loads the existing artifact, shows it in an editable Streamlit table or form, lets the user save changes, and records whether the artifact has been confirmed. The pipeline inserts review checkpoints between generation steps, so users can confirm quality before continuing.

This approach keeps the first version practical:

- No database.
- No full timeline editor.
- No video-synchronized subtitle editing.
- No rewrite of the translation, subtitle, or TTS engines.

## Scope For Version 1

Version 1 includes:

- Review and edit terminology terms: `src`, `tgt`, and `note`.
- Review and edit translation rows: `Source` and `Translation`.
- Review and edit subtitle rows from the display subtitle split file.
- Review and edit audio/TTS task rows: `text` and `origin`, while preserving timing columns.
- Save edits back to the existing workspace artifact files.
- Backup the previous artifact before saving.
- Mark each review stage as `pending`, `confirmed`, or `stale`.
- Invalidate downstream review stages when an upstream artifact changes.
- Split the current Streamlit pipeline into smaller steps so review checkpoints can appear naturally.
- Provide buttons to confirm an artifact and continue the next stage.

Version 1 does not include:

- Per-word or waveform-level subtitle timing edits.
- Video preview synchronized with each subtitle row.
- Comments, assignments, or multi-user review.
- Side-by-side version diff UI.
- AI rewrite suggestions inside the review table.
- Batch review UI for many videos at once.

Those can be added later once the artifact and checkpoint model is stable.

## Review Stages

### Terminology Review

Runs after `_4_1_summarize.get_summary()` and before `_4_2_translate.translate_all()`.

The page loads `output/log/terminology.json`, displays the `terms` list, and preserves other JSON keys such as `theme`. Users can add, delete, and edit terms. Confirming terminology means the translation step can use the reviewed glossary.

Saving terminology marks translation, subtitles, and TTS text as `stale`.

### Translation Review

Runs after `_4_2_translate.translate_all()` and before `_5_split_sub.split_for_sub_main()`.

The page loads `output/log/translation_results.xlsx`. Users can edit translation rows while keeping the source rows visible. Confirming translation means subtitle splitting can use the reviewed text.

Saving translation marks subtitles and TTS text as `stale`.

### Subtitle Review

Runs after `_5_split_sub.split_for_sub_main()` and before `_6_gen_sub.align_timestamp_main()`.

The page loads `output/log/translation_results_for_subtitles.xlsx` for display subtitles. Users can edit `Source` and `Translation` rows. If the display subtitle file and `output/log/translation_results_remerged.xlsx` have the same row count, saving subtitle edits updates matching rows in both files. If the row counts differ, saving updates only the display subtitle file and marks TTS text as `stale`, so the audio subtitle source is regenerated before dubbing continues.

Confirming subtitles allows the app to regenerate SRT files through `_6_gen_sub.align_timestamp_main()`.

Saving subtitles marks TTS text as `stale`.

### TTS Text Review

Runs after `_8_1_audio_task.gen_audio_task_main()` and before `_8_2_dub_chunks.gen_dub_chunks()`.

The page loads `output/audio/tts_tasks.xlsx`. Users can edit the text that will be spoken by TTS, while timing fields remain visible but not the primary editing target. Confirming TTS text allows reference extraction, chunk generation, audio generation, and final dubbing to continue.

Saving TTS text does not invalidate later review stages in version 1 because there is no later human review checkpoint.

## Data Model

Each task workspace gets:

```text
workspace/jobs/<job_id>/
  artifacts/
    reviews/
      review_status.yaml
      backups/
        <stage>-<timestamp>.<ext>
```

`review_status.yaml` stores:

```yaml
stages:
  terminology:
    status: "pending|confirmed|stale"
    artifact: "output/log/terminology.json"
    confirmed_at: ""
    updated_at: ""
  translation:
    status: "pending|confirmed|stale"
    artifact: "output/log/translation_results.xlsx"
    confirmed_at: ""
    updated_at: ""
  subtitles:
    status: "pending|confirmed|stale"
    artifact: "output/log/translation_results_for_subtitles.xlsx"
    confirmed_at: ""
    updated_at: ""
  tts_text:
    status: "pending|confirmed|stale"
    artifact: "output/audio/tts_tasks.xlsx"
    confirmed_at: ""
    updated_at: ""
```

The status file is workspace-local and should not affect other tasks.

## Streamlit UX

The sidebar continues to own task workspace selection. The main app adds a review workbench section after task selection and before final downloads.

Recommended layout:

- A compact status row showing the four review stages.
- Tabs for Terminology, Translation, Subtitles, and TTS Text.
- Each tab shows a file-missing state when the upstream step has not generated the artifact yet.
- Editable tables use `st.data_editor` for tabular files.
- Terminology review uses a table for `terms` plus a small read-only or editable area for `theme`.
- Buttons per tab:
  - Save changes
  - Confirm
  - Mark as needs review

The pipeline buttons should communicate the next required action. For example, after terminology is generated, the next visible action is to review terminology before translation continues.

## Pipeline Flow

The text workflow should be split into review-aware steps:

1. ASR
2. sentence segmentation
3. terminology generation
4. terminology review
5. translation
6. translation review
7. subtitle split
8. subtitle review
9. SRT generation
10. subtitle burn-in

The audio workflow should be split into:

1. TTS task generation
2. TTS text review
3. dub chunk generation
4. reference audio extraction
5. TTS audio generation
6. full audio merge
7. final video merge

For the first version, review checkpoints are handled by Streamlit UI state and the workspace status file. The background runner should stop after a generation step if the next checkpoint needs review.

## Invalidation Rules

When a user saves an upstream artifact, downstream stages become stale:

- Terminology save invalidates translation, subtitles, and TTS text.
- Translation save invalidates subtitles and TTS text.
- Subtitle save invalidates TTS text.
- TTS text save invalidates no review stage.

Stale does not delete files. It tells the user that later artifacts were generated from older content and should be regenerated or reconfirmed.

## Error Handling

If an artifact file is missing, the tab shows a clear waiting state and does not create a blank artifact silently.

If a file cannot be parsed, the tab shows the parse error and leaves the file unchanged.

Before saving, the workbench creates a backup copy in `artifacts/reviews/backups/`. If saving fails, the original artifact remains available.

If a user edits table columns that are required by downstream code, the workbench validates required columns before writing.

If no active task workspace exists, the review workbench should show a prompt to create or select a task first.

## Testing

Add focused tests for:

- Creating a default `review_status.yaml`.
- Marking a stage confirmed.
- Saving terminology while preserving non-term JSON keys.
- Saving translation Excel and creating a backup.
- Invalidating downstream stages after upstream saves.
- Loading review artifacts through workspace-aware paths.

Manual verification:

- Create a task and run through terminology generation.
- Edit and confirm terminology, then continue translation.
- Edit and confirm translation, then continue subtitle split.
- Edit subtitle rows, regenerate SRT files, and confirm the SRT reflects edits.
- Generate TTS tasks, edit TTS text, continue dubbing, and confirm audio tasks use the edited text.

## Implementation Notes

Add a small review module rather than embedding all review logic in `st.py`.

Suggested module responsibilities:

- `core/review.py`: status file, artifact loading/saving, backups, invalidation rules.
- `core/st_utils/review_section.py`: Streamlit tabs and review controls.
- `st.py`: wire the review section and split workflow steps.

The first implementation should keep artifact schemas close to the existing files so the current core pipeline remains the source of truth.
