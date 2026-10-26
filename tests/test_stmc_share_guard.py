"""Offline tests of the real STMC sharing guard and shell launcher.

All upstream STMC files are synthetic and disposable. The fake 'python' binary
does not import Gradio, torch, models or start a listener. No pod access.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stmc_share_guard", ROOT / "envs" / "disable_stmc_share.py"
)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ShareGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="motiongen_share_guard_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "app_config.py"

    def test_true_variants_are_disabled_preserving_unrelated_code_and_permissions(self):
        for assign in ("SHARE = True", "SHARE=True", "SHARE  =  True  # STMC public link"):
            with self.subTest(assign=assign):
                self.config.write_text("TITLE = 'demo'\n" + assign + "\nOTHER = 7\n")
                self.config.chmod(0o640)
                self.assertTrue(guard.disable_public_share(self.config))
                data = self.config.read_text()
                self.assertIn("SHARE", data)
                self.assertNotIn("True", data)
                self.assertIn("OTHER = 7\n", data)
                self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)
                self.assertFalse(guard.disable_public_share(self.config))
                self.assertEqual(self.config.read_text(), data)
                self.assertEqual(list(self.root.glob(".app_config.share-*.tmp")), [])

    def test_valid_existing_false_remains_untouched(self):
        original = "SHARE = False  # sharing disabled already\nX = 1\n"
        self.config.write_text(original)
        self.assertFalse(guard.disable_public_share(self.config))
        self.assertEqual(self.config.read_text(), original)

    def test_ambiguous_or_missing_share_setting_fails_without_edit(self):
        for code in (
            "APP = 'demo'\n",
            "SHARE = True\nSHARE = False\n",
            "SHARE = os.getenv('PUBLIC', True)\n",
            "SHARE: bool = True\n",
            "SHARE = True; print('ignored')\n",
            "if True:\n    SHARE = True\n",
            "SHARE = True\nif True:\n    SHARE = True\n",
            "def fn():\n    SHARE = True\n",
            "SHARE = [True][0]\n",
            "SHARE = True, False\n",
            "SHARE = True\nBROKEN = (\n",
        ):
            with self.subTest(code=code):
                self.config.write_text(code)
                with self.assertRaises((ValueError, SyntaxError)):
                    guard.disable_public_share(self.config)
                self.assertEqual(self.config.read_text(), code)
                self.assertEqual(list(self.root.glob(".app_config.share-*.tmp")), [])

    def test_symlinked_config_fails_and_does_not_modify_target(self):
        real = self.root / "real_config.py"
        real.write_text("SHARE = True\n")
        self.config.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "regular file"):
            guard.disable_public_share(self.config)
        self.assertEqual(real.read_text(), "SHARE = True\n")
        self.assertTrue(self.config.is_symlink())


class StmcLauncherFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="motiongen_stmc_fake_launch_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "envs" / "stmc" / "bin").mkdir(parents=True)
        (self.root / "repos" / "stmc").mkdir(parents=True)
        (self.root / "fake-bin").mkdir()
        shutil.copy2(ROOT / "launch_stmc.sh", self.root / "launch_stmc.sh")
        shutil.copy2(ROOT / "envs" / "common_env.sh", self.root / "envs" / "common_env.sh")
        shutil.copy2(
            ROOT / "envs" / "disable_stmc_share.py",
            self.root / "envs" / "disable_stmc_share.py",
        )
        (self.root / "envs" / "stmc" / "bin" / "activate").write_text(
            "# Synthetic activation; no environment installation\n"
        )
        self.marker = self.root / "synthetic_python_invoked"
        self.mock_python = self.root / "fake-bin" / "python"
        self.mock_python.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$STMC_TEST_LAUNCHED\"\n",
        )
        self.mock_python.chmod(0o755)
        self.config = self.root / "repos" / "stmc" / "app_config.py"

    def launch(self):
        env = os.environ.copy()
        env["PATH"] = str(self.root / "fake-bin") + os.pathsep + env.get("PATH", "")
        env["STMC_TEST_LAUNCHED"] = str(self.marker)
        return subprocess.run(
            ["bash", str(self.root / "launch_stmc.sh")],
            cwd=self.root, env=env, capture_output=True, text=True,
            check=False, timeout=10,
        )

    def test_launcher_disables_unspaced_true_then_starts_fake_process(self):
        self.config.write_text("SHARE=True\n")
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.config.read_text(), "SHARE=False\n")
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.marker.read_text(), "app.py\n")
        self.assertIn("SHARE=False verified", result.stdout)

    def test_launcher_accepts_already_disabled_config(self):
        self.config.write_text("SHARE = False\n")
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.config.read_text(), "SHARE = False\n")
        self.assertTrue(self.marker.exists())

    def test_launcher_refuses_unrecognised_setting_without_starting(self):
        self.config.write_text("SHARE = get_configuration()\n")
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to launch STMC", result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.config.read_text(), "SHARE = get_configuration()\n")

    def test_launcher_refuses_missing_config_without_starting(self):
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to launch STMC", result.stderr)
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
