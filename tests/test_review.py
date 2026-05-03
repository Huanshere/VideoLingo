import tempfile
import unittest
from pathlib import Path

from core import review, workspace


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text("display_language: en\n", encoding="utf-8")
        self.job = workspace.create_job(
            name="Review Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        workspace.set_active_workspace(self.job["path"])

    def tearDown(self):
        workspace.clear_active_workspace()

    def test_default_review_status_is_created_in_active_workspace(self):
        status = review.load_status()

        status_path = (
            Path(self.job["path"])
            / "artifacts"
            / "reviews"
            / "review_status.yaml"
        )
        self.assertTrue(status_path.is_file())
        self.assertEqual(status["stages"]["terminology"]["status"], "pending")
        self.assertEqual(
            status["stages"]["translation"]["artifact"],
            "output/log/translation_results.xlsx",
        )

    def test_mark_confirmed_records_timestamp(self):
        review.mark_confirmed("terminology")
        status = review.load_status()

        self.assertEqual(status["stages"]["terminology"]["status"], "confirmed")
        self.assertTrue(status["stages"]["terminology"]["confirmed_at"])
