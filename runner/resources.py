"""Locate runner resources in a checkout or in an installed wheel.

The editable repository keeps prompts and research beside :mod:`runner` so they
remain easy to review.  ``setup.py`` copies those resources under
``runner/data`` only in the build directory; an installed wheel therefore has
the same layout without relying on the caller's current working directory.
"""

from __future__ import annotations

from pathlib import Path


_REQUIRED_DIRECTORIES = ("agents", "skills", "knowledge")


def resource_root() -> Path:
    """Return the directory containing bundled prompts, skills, and knowledge.

    Prefer the repository root while running from a source checkout.  In an
    installed distribution, use the package-local ``data`` directory created
    at build time.  The explicit checks keep the result independent of CWD and
    make a damaged installation fail with an actionable error.
    """
    package_dir = Path(__file__).resolve().parent
    checkout_root = package_dir.parent
    bundled_root = package_dir / "data"

    for candidate in (checkout_root, bundled_root):
        if all((candidate / name).is_dir() for name in _REQUIRED_DIRECTORIES):
            return candidate

    expected = ", ".join(_REQUIRED_DIRECTORIES)
    raise FileNotFoundError(
        "Book Genesis resources are unavailable. Expected "
        f"{expected} under {checkout_root} (checkout) or {bundled_root} (installed wheel)."
    )
