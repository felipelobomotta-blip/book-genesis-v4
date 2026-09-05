"""Build hooks for the self-contained Book Genesis wheel.

Project metadata stays in ``pyproject.toml``.  This hook stages repository
resources into the wheel build directory, avoiding a second editable copy in
the source tree.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


RESOURCE_DIRECTORIES = ("agents", "knowledge", "skills")


class BuildPyWithResources(_build_py):
    """Copy runtime Markdown/YAML resources into ``runner/data`` at build time."""

    def run(self) -> None:
        super().run()
        source_root = Path(__file__).resolve().parent
        build_root = Path(self.build_lib).resolve()
        destination_root = build_root / "runner" / "data"
        # A repeated wheel build must not retain a prompt deleted from source.
        # Only remove the generated resource directory inside this build tree.
        if destination_root.exists():
            resolved = destination_root.resolve()
            if not resolved.is_relative_to(build_root) or resolved == source_root:
                raise ValueError(f"Unsafe generated resource destination: {destination_root}")
            shutil.rmtree(resolved)
        for name in RESOURCE_DIRECTORIES:
            source = source_root / name
            if not source.is_dir():
                raise FileNotFoundError(f"Required package resource directory is missing: {source}")
            shutil.copytree(source, destination_root / name, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildPyWithResources})
