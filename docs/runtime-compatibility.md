# Runtime compatibility follow-ups

This change addresses distinct compatibility gaps discussed in PR #590 without
hardcoded personal network settings or unrelated provider/translation changes.

## Whisper model cache

Resolve complete explicit local directories, then the configured project Hub
cache and the global Hub cache with `local_files_only=True`. Pass the resulting
directory to WhisperX. If neither cache has a complete snapshot, fetch missing
files with the installed loader's standard endpoint configuration. Preserve model
aliases by letting faster-whisper resolve them rather than constructing repository
names. An incomplete explicitly selected directory fails clearly.

Remove per-segment ICMP mirror races, late global endpoint mutation, and the fixed
obsolete Torch warning. Missing project cache is normal when global cache is
complete. This does not keep models resident in GPU memory or guarantee that
other WhisperX components (such as alignment models) need no downloads.

## Launcher logs

Initialize UTF-8 without BOM and stream subsequent lines through the same encoding
with Windows PowerShell 5.1. The logger reads stdin incrementally and flushes each
line. It uses the LOGFILE environment variable so paths are not injected into
PowerShell expressions. Both Conda and shared-venv launch paths use it. Existing
mixed-encoding log files are not rewritten.

## GPT-SoVITS startup

Use the read-only FastAPI schema endpoint instead of `/ping`, which is absent in
upstream api_v2.py. Require synthesis and both model-selection routes. An occupied
port alone, an unrelated 200 response, a redirect, or an HTTP error is insufficient.
Requests bypass environment proxies for loopback, have explicit timeouts, and do
not call control or synthesis endpoints. Detect a child process that exits during
startup. Use Popen's cwd rather than changing the entire application's directory.

Schema availability proves API shape, not successful synthesis. Custom builds
with OpenAPI disabled are not accepted automatically. The initial wait remains
50 seconds with bounded probes (requests timeouts are per socket operation, not
a strict whole-operation deadline). No existing service is restarted by checks.

## Legacy task tables

Parse task-cell Python literals with ast.literal_eval, accepting only finite
numeric `np.float32(...)` and `np.float64(...)` wrappers from older NumPy-generated
tables. Other function calls, imports and expressions are rejected. New tables
continue to contain plain floats as fixed in PR #599. Both dubbing generation
and final audio assembly readers use the same parser. No historical files are
migrated or overwritten.

## Verification

`python -m pytest -q tests/test_runtime_compatibility.py tests/test_download_proxy.py`

Tests cover cache selection without models/network, proxy discovery/overrides,
legacy literals and rejected executable expressions, SoVITS schema/status/child
exit behavior, and an actual Windows PowerShell UTF-8 stdin/console/file roundtrip
using the launcher's header command. They do not start Streamlit, SoVITS, download
media, install dependencies or invoke paid APIs. Real synthesis and live site
downloads remain runtime checks for users of those optional integrations.
