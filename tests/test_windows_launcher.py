"""Exercise the launcher's version probes through the real Windows batch parser."""
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name != "nt", reason="Requires the Windows CMD parser")
@pytest.mark.parametrize("branch", ["shared", "project", "conda"])
@pytest.mark.parametrize("version,expected", [((3, 10), 1), ((3, 12), 0), ((3, 13), 1)])
def test_batch_version_probes_with_delayed_expansion(tmp_path, branch, version, expected):
    source = (ROOT / "OneKeyStart.bat").read_text(encoding="utf-8")
    probes = re.findall(r'-c "([^"]*sys\.version_info[^\"]*)"', source)
    assert len(probes) == 3
    probe = dict(zip(("shared", "project", "conda"), probes))[branch]
    # Keep the actual launcher expression, including any CMD-sensitive characters.
    # Override only the reported version so unsupported interpreters are tested too.
    code = f"import sys; sys.version_info={version!r}; {probe}"
    directory = tmp_path / "path with spaces"
    directory.mkdir()
    script = directory / "probe.bat"
    script.write_text(
        "@echo off\nsetlocal EnableExtensions EnableDelayedExpansion\n"
        "if 1==1 (\n"
        f'    "{sys.executable}" -c "{code}"\n'
        "    exit /b !errorlevel!\n)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(script)],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    assert not result.stderr, result.stderr
