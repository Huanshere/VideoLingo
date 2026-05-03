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

    def test_save_terminology_preserves_theme_and_invalidates_downstream(self):
        import json

        path = Path(self.job["path"]) / "output" / "log"
        path.mkdir(parents=True, exist_ok=True)
        terminology = path / "terminology.json"
        terminology.write_text(
            json.dumps(
                {
                    "theme": "Physics lecture",
                    "terms": [{"src": "force", "tgt": "力", "note": "physics"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        review.mark_confirmed("translation")

        review.save_terminology(
            [{"src": "energy", "tgt": "能量", "note": "physics"}],
            theme="Physics lecture",
        )

        saved = json.loads(terminology.read_text(encoding="utf-8"))
        self.assertEqual(saved["theme"], "Physics lecture")
        self.assertEqual(saved["terms"][0]["src"], "energy")
        status = review.load_status()
        self.assertEqual(status["stages"]["translation"]["status"], "stale")
        backups = list(
            (
                Path(self.job["path"])
                / "artifacts"
                / "reviews"
                / "backups"
            ).glob("terminology-*.json")
        )
        self.assertEqual(len(backups), 1)

    def test_save_table_creates_backup_and_validates_required_columns(self):
        import pandas as pd

        path = Path(self.job["path"]) / "output" / "log"
        path.mkdir(parents=True, exist_ok=True)
        artifact = path / "translation_results.xlsx"
        pd.DataFrame({"Source": ["hello"], "Translation": ["你好"]}).to_excel(
            artifact, index=False
        )

        review.save_table(
            "translation",
            pd.DataFrame({"Source": ["hello"], "Translation": ["您好"]}),
            required_columns=("Source", "Translation"),
        )

        saved = pd.read_excel(artifact)
        self.assertEqual(saved.at[0, "Translation"], "您好")
        backups = list(
            (
                Path(self.job["path"])
                / "artifacts"
                / "reviews"
                / "backups"
            ).glob("translation-*.xlsx")
        )
        self.assertEqual(len(backups), 1)

    def test_save_table_rejects_missing_required_columns(self):
        import pandas as pd

        with self.assertRaises(ValueError):
            review.save_table(
                "translation",
                pd.DataFrame({"Source": ["hello"]}),
                required_columns=("Source", "Translation"),
            )
