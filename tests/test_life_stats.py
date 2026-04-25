import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "life_stats.py"


class LifeStatsCliTest(unittest.TestCase):
    def run_cli(self, *args):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "MEMENTO_MORI_STATE": str(state), "PYTHONUTF8": "1"}
            return subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )

    def test_setup_outputs_life_overview(self):
        result = self.run_cli("setup", "--birthdate", "1995-03-15", "--life-expectancy-years", "85")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["birthdate"], "1995-03-15")
        self.assertIn("weeks_left", payload)
        self.assertEqual(len(payload["progress_bar"]), 32)

    def test_journal_preserves_raw_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "MEMENTO_MORI_STATE": str(state), "PYTHONUTF8": "1"}
            subprocess.run(
                [sys.executable, str(SCRIPT), "setup", "--birthdate", "1995-03-15", "--life-expectancy-years", "85"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "journal",
                    "--week",
                    "2026-W17",
                    "--entry",
                    "Original sentence.",
                    "--summary",
                    "Short summary.",
                ],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["entry"]["raw"], "Original sentence.")
            self.assertEqual(payload["entry"]["summary"], "Short summary.")

    def test_stats_uses_calendar_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "MEMENTO_MORI_STATE": str(state), "PYTHONUTF8": "1"}
            subprocess.run(
                [sys.executable, str(SCRIPT), "setup", "--birthdate", "1995-03-15", "--life-expectancy-years", "85"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPT), "journal", "--week", "2026-W17", "--entry", "One entry.", "--summary", "One entry."],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--last-n", "4"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["stats"]["weeks_considered"], 4)
            self.assertLess(payload["stats"]["coverage_pct"], 100)

    def test_share_outputs_text_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "MEMENTO_MORI_STATE": str(state), "PYTHONUTF8": "1"}
            subprocess.run(
                [sys.executable, str(SCRIPT), "setup", "--birthdate", "1995-03-15", "--life-expectancy-years", "85"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPT), "journal", "--week", "2026-W17", "--entry", "Built a share card.", "--summary", "Built a share card."],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "share"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertIn("我的人生周历", result.stdout)
            self.assertIn("Generated by Memento Mori for OpenClaw", result.stdout)
            self.assertIn("Built a share card.", result.stdout)

    def test_checkin_returns_style_opening(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "MEMENTO_MORI_STATE": str(state), "PYTHONUTF8": "1"}
            subprocess.run(
                [sys.executable, str(SCRIPT), "setup", "--birthdate", "1995-03-15", "--life-expectancy-years", "85"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "checkin", "--style", "sharp"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["checkin_style"], "sharp")
            self.assertIn("你没有失去一天", payload["suggested_opening"])


if __name__ == "__main__":
    unittest.main()
