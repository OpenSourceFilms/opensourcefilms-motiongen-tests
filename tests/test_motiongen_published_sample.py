"""Offline acceptance of the published, synthetic Kimodo motion sample.

No model weights, GPU, ComfyUI or private footage required. No motion quality
or human-identification claims. The sample's numeric schema must remain stable.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "outputs/kimodo/smoke_test_walk_wave.npz"
EXPECTED = {
    "local_rot_mats": ((150, 77, 3, 3), np.dtype("float32")),
    "global_rot_mats": ((150, 77, 3, 3), np.dtype("float32")),
    "posed_joints": ((150, 77, 3), np.dtype("float32")),
    "root_positions": ((150, 3), np.dtype("float32")),
    "smooth_root_pos": ((150, 3), np.dtype("float32")),
    "foot_contacts": ((150, 6), np.dtype("bool")),
    "global_root_heading": ((150, 2), np.dtype("float32")),
}


class PublishedMotionArtifact(unittest.TestCase):
    def test_npz_is_present_and_contains_no_extra_fields(self):
        self.assertTrue(SAMPLE.is_file())
        with np.load(SAMPLE, allow_pickle=False) as archive:
            self.assertEqual(set(archive.files), set(EXPECTED))
            self.assertEqual(len(archive.files), 7)

    def test_all_field_shapes_and_dtypes(self):
        with np.load(SAMPLE, allow_pickle=False) as archive:
            for key, (shape, dtype) in EXPECTED.items():
                with self.subTest(field=key):
                    array = archive[key]
                    self.assertEqual(array.shape, shape)
                    self.assertEqual(array.dtype, dtype)
                    self.assertNotEqual(array.dtype.kind, "O",
                                        "pickle/object arrays are not accepted")

    def test_float_fields_have_no_nan_or_inf(self):
        with np.load(SAMPLE, allow_pickle=False) as archive:
            for key in EXPECTED:
                array = archive[key]
                if np.issubdtype(array.dtype, np.floating):
                    with self.subTest(field=key):
                        self.assertTrue(np.isfinite(array).all())

    def test_all_fields_have_same_150_frame_time_base(self):
        with np.load(SAMPLE, allow_pickle=False) as archive:
            for key in EXPECTED:
                self.assertEqual(archive[key].shape[0], 150, key)

    def test_foot_contacts_are_boolean(self):
        with np.load(SAMPLE, allow_pickle=False) as archive:
            contacts = archive["foot_contacts"]
            self.assertEqual(contacts.dtype, np.dtype("bool"))
            self.assertEqual(contacts.shape[1], 6)

    def test_shell_launchers_parse_without_execution(self):
        paths = [
            "launch_kimodo.sh", "launch_stmc.sh",
            "run_genmo_example.sh", "run_smoke_tests.sh",
            "envs/common_env.sh",
        ]
        for name in paths:
            with self.subTest(script=name):
                result = subprocess.run(
                    ["bash", "-n", str(ROOT / name)],
                    capture_output=True, text=True, timeout=10, check=False
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
