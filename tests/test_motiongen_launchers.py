"""Offline smoke-launcher failure tests using fake executables only.

Nothing imports Kimodo, GENMO, STMC, torch or CUDA. Scripts and launch
fixtures are copied into a disposable directory before being executed.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MotiongenLauncherSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="motiongen_fake_launch_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "envs").mkdir(parents=True)
        for name in ("run_smoke_tests.sh", "run_genmo_example.sh"):
            shutil.copy2(ROOT / name, self.root / name)
        shutil.copy2(ROOT / "envs" / "common_env.sh", self.root / "envs" / "common_env.sh")
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()

    def stub(self, relpath: str, returncode: int):
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/bin/sh\n"
            "echo simulated-generator-result\n"
            f"exit {returncode}\n", encoding="utf-8"
        )
        path.chmod(0o755)

    def run_launcher(self, name: str, *args: str):
        env = os.environ.copy()
        env["PATH"] = str(self.fake_bin) + os.pathsep + env.get("PATH", "")
        return subprocess.run(
            ["bash", str(self.root / name), *args],
            cwd=self.root, env=env, capture_output=True, text=True,
            timeout=15, check=False,
        )

    def test_kimodo_failure_propagates_and_logs_created(self):
        self.stub("envs/kimodo/bin/kimodo_gen", 41)
        result = self.run_launcher("run_smoke_tests.sh", "kimodo")
        self.assertEqual(result.returncode, 41, result.stdout + result.stderr)
        self.assertIn("simulated-generator-result",
                      (self.root / "logs" / "kimodo_smoke_test.log").read_text())

    def test_all_must_not_hide_a_failed_kimodo_run(self):
        self.stub("envs/kimodo/bin/kimodo_gen", 41)
        result = self.run_launcher("run_smoke_tests.sh", "all")
        self.assertEqual(result.returncode, 41, result.stdout + result.stderr)
        self.assertNotIn("Skipping genmo", result.stdout)

    def test_stmc_failure_must_not_claim_outputs_exist(self):
        self.stub("envs/stmc/bin/python", 42)
        (self.root / "repos" / "stmc").mkdir(parents=True)
        result = self.run_launcher("run_smoke_tests.sh", "stmc")
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertNotIn("Outputs land", result.stdout)
        self.assertIn("simulated-generator-result",
                      (self.root / "logs" / "stmc_smoke_test.log").read_text())

    def test_genmo_smoke_failure_propagates(self):
        self.stub("envs/genmo/bin/python", 43)
        (self.root / "repos" / "GENMO").mkdir(parents=True)
        result = self.run_launcher("run_smoke_tests.sh", "genmo", "synthetic.mp4")
        self.assertEqual(result.returncode, 43, result.stdout + result.stderr)
        self.assertIn("simulated-generator-result",
                      (self.root / "logs" / "genmo_smoke_test.log").read_text())

    def test_genmo_example_failure_must_not_claim_output(self):
        self.stub("fake-bin/python", 44)
        (self.root / "envs" / "genmo" / "bin").mkdir(parents=True)
        (self.root / "envs" / "genmo" / "bin" / "activate").write_text(
            "# fake activation: no external package/environment\n"
        )
        (self.root / "repos" / "GENMO").mkdir(parents=True)
        source = self.root / "fabricated.mp4"
        source.write_bytes(b"NOT-REAL-VIDEO")
        result = self.run_launcher("run_genmo_example.sh", str(source))
        self.assertEqual(result.returncode, 44, result.stdout + result.stderr)
        self.assertNotIn("Output written", result.stdout)
        self.assertIn("simulated-generator-result",
                      (self.root / "logs" / "genmo_example.log").read_text())

    def test_valid_success_path_does_not_acquire_new_dependencies(self):
        self.stub("envs/kimodo/bin/kimodo_gen", 0)
        result = self.run_launcher("run_smoke_tests.sh", "all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Skipping genmo", result.stdout)
        self.assertIn("simulated-generator-result",
                      (self.root / "logs" / "kimodo_smoke_test.log").read_text())


if __name__ == "__main__":
    unittest.main()
