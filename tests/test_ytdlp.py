import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import _1_ytdlp


class FindVideoFilesTests(unittest.TestCase):
    @patch.object(_1_ytdlp, "load_key", return_value=["mp4"])
    def test_keeps_output_prefixed_inputs_and_ignores_generated_videos(self, _):
        for input_name in ("output.mp4", "output tutorial.mp4", "OUTPUT.MP4", "output_sub tutorial.mp4"):
            with self.subTest(input_name=input_name), tempfile.TemporaryDirectory() as temp_dir:
                previous_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    output_dir = Path("output")
                    output_dir.mkdir()
                    for filename in (input_name, "output_sub.mp4", "output_dub.mp4"):
                        (output_dir / filename).touch()

                    result = _1_ytdlp.find_video_files()

                    self.assertEqual(Path(result).name, input_name)
                finally:
                    os.chdir(previous_cwd)

    @patch.object(_1_ytdlp, "load_key", return_value=["mp4"])
    def test_absolute_directory_and_case_insensitive_generated_names(self, _):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "custom output"
            output.mkdir()
            for filename in ("output tutorial.MP4", "OUTPUT_SUB.MP4", "Output_Dub.mp4"):
                (output / filename).touch()
            (output / "folder.mp4").mkdir()
            self.assertEqual(Path(_1_ytdlp.find_video_files(str(output))).name, "output tutorial.MP4")

    @patch.object(_1_ytdlp, "load_key", return_value=["mp4"])
    def test_multiple_real_inputs_remain_ambiguous(self, _):
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename in ("output.mp4", "other.mp4"):
                (Path(temp_dir) / filename).touch()
            with self.assertRaisesRegex(ValueError, "found 2"):
                _1_ytdlp.find_video_files(temp_dir)

    @patch.object(_1_ytdlp, "load_key", return_value=["mp4"])
    def test_generated_videos_are_not_treated_as_inputs(self, _):
        with tempfile.TemporaryDirectory() as temp_dir:
            previous_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                output_dir = Path("output")
                output_dir.mkdir()
                (output_dir / "output_sub.mp4").touch()
                (output_dir / "output_dub.mp4").touch()

                with self.assertRaisesRegex(ValueError, "found 0"):
                    _1_ytdlp.find_video_files()
            finally:
                os.chdir(previous_cwd)


if __name__ == "__main__":
    unittest.main()
