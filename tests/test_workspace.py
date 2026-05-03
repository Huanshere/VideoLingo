import os
import tempfile
import unittest
from pathlib import Path

from ruamel.yaml import YAML

from core import workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text(
            "display_language: en\napi:\n  key: ''\n", encoding="utf-8"
        )
        workspace.clear_active_workspace()

    def tearDown(self):
        workspace.clear_active_workspace()

    def test_create_job_writes_metadata_and_config_snapshot(self):
        job = workspace.create_job(
            name="My Video!",
            source_type="upload",
            source_path="input.mp4",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )

        self.assertTrue(Path(job["path"]).is_dir())
        self.assertTrue((Path(job["path"]) / "output").is_dir())
        self.assertTrue((Path(job["path"]) / "job.yaml").is_file())
        self.assertTrue((Path(job["path"]) / "config.snapshot.yaml").is_file())
        self.assertEqual(job["name"], "My Video!")
        self.assertEqual(job["source"]["type"], "upload")

    def test_active_workspace_resolves_output_path(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        workspace.set_active_workspace(job["path"])

        resolved = workspace.output_path("log", "file.txt")

        self.assertEqual(
            os.fspath(resolved),
            str(Path(job["path"]) / "output" / "log" / "file.txt"),
        )

    def test_legacy_output_path_without_active_workspace(self):
        workspace.clear_active_workspace()

        self.assertEqual(
            os.fspath(workspace.output_path("log", "file.txt")),
            "output/log/file.txt",
        )

    def test_archive_job_marks_status_without_deleting_files(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )

        workspace.archive_job(job["path"])
        loaded = workspace.load_job(job["path"])

        self.assertEqual(loaded["status"], "archived")
        self.assertTrue(Path(job["path"]).exists())

    def test_config_snapshot_is_independent_from_global_config(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        self.config_path.write_text(
            "display_language: zh-CN\napi:\n  key: changed\n",
            encoding="utf-8",
        )

        yaml = YAML()
        snapshot = yaml.load(
            (Path(job["path"]) / "config.snapshot.yaml").read_text(encoding="utf-8")
        )

        self.assertEqual(snapshot["display_language"], "en")
        self.assertEqual(snapshot["api"]["key"], "")
