"""Wheel packaging regressions.

The smoke test deliberately runs in a temporary directory with only the
installed wheel on ``sys.path``.  It catches accidental references to a
developer checkout and verifies both pipeline manifests and agent templates.
"""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]


class WheelResourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-wheel-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_wheel_contains_runtime_resources_and_loads_away_from_checkout(self) -> None:
        wheelhouse = self.tempdir / "wheelhouse"
        wheelhouse.mkdir()
        build = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--no-cache-dir",
                "--wheel-dir",
                str(wheelhouse),
                ".",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(0, build.returncode, msg=build.stderr)
        wheels = list(wheelhouse.glob("book_genesis-*.whl"))
        self.assertEqual(1, len(wheels), msg=build.stdout)
        wheel = wheels[0]

        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
        for required in (
            "runner/data/agents/book-writer.md",
            "runner/data/knowledge/bestseller-dna.md",
            "runner/data/skills/book-genesis-codex/references/pipeline/manifest.yaml",
            "runner/data/skills/book-bestseller-studio/references/agent-registry.yaml",
        ):
            self.assertIn(required, names)

        site_packages = self.tempdir / "site-packages"
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(site_packages), str(wheel)],
            cwd=self.tempdir,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(0, install.returncode, msg=install.stderr)

        script = (
            "from pathlib import Path\n"
            "import sys\n"
            f"sys.path.insert(0, {str(site_packages)!r})\n"
            "from runner.resources import resource_root\n"
            "from runner.filesystem import load_manifest\n"
            "from runner.chapter import writer_prompt\n"
            "from runner.constants import load_genre_profile\n"
            "root = resource_root()\n"
            "assert root == Path(__import__('runner').__file__).resolve().parent / 'data', root\n"
            "assert (root / 'agents' / 'book-writer.md').is_file()\n"
            "assert len(load_manifest()) > 0\n"
            "prompt = writer_prompt('isolated brief', 1, 'thriller', load_genre_profile('thriller'))\n"
            "assert 'RUNNER CONTRACT' in prompt and 'isolated brief' in prompt\n"
        )
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        smoke = subprocess.run(
            [sys.executable, "-I", "-c", script],
            cwd=self.tempdir,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, smoke.returncode, msg=smoke.stderr)


if __name__ == "__main__":
    unittest.main()
