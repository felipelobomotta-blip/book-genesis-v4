"""Build a deterministic, local interface sample with the current reader.

This creates fixture prose and fixture history only. It does not call a provider,
evaluate a manuscript, or represent a real Book Genesis run.

When this file lives in a repository's ``scripts/`` directory, it imports that
checkout's ``runner`` package. During standalone preparation, pass ``--source``
with a checkout path instead. The generated HTML never includes that path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


CHAPTERS = {
    1: (
        "# The Lantern Index\n\n"
        "At 2:17 a.m., Mara found a library card that had been returned tomorrow. "
        "The name on it was her own.\n\n"
        "She did not touch the ink. The ink had already begun to move.\n",
        "# The Lantern Index\n\n"
        "At 2:17 a.m., Mara found a library card stamped with tomorrow's date. "
        "The name on it was her own.\n\n"
        "She left it on the desk. Outside, the return chute clicked once, then twice.\n",
    ),
    2: (
        "# The Return Chute\n\n"
        "The next card carried a name Mara did not know, and a date that had already passed. "
        "She locked the archive door.\n\n"
        "Behind the wall, paper slid through metal with the patience of rain.\n",
        "# The Return Chute\n\n"
        "The next card carried a name Mara did not know and a date that had already passed. "
        "She locked the archive door, then listened.\n\n"
        "Behind the wall, paper slid through metal with the patience of rain. The chute stopped when she said the name aloud.\n",
    ),
}


def _source_root(value: str) -> Path:
    root = Path(value).resolve() if value else Path(__file__).resolve().parents[1]
    if not (root / "runner" / "review.py").is_file():
        raise SystemExit("Could not find runner/review.py. Run from the repository or pass --source PATH.")
    return root


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _state() -> str:
    return """# Project State
title: "Scripted reader interface sample"
idea: "Fixture data for the local reader UI"
language: "en"
genre: "fiction"
audience: "interface reviewers"
adapter: "fixture"
model_name: "none"
current_phase: "Phase 4: Adversarial Audit"
current_gate: "audit"
status: "awaiting_revision"
"""


def _history(project: Path, number: int, initial: str, accepted: str) -> None:
    folder = project / "manuscript" / "chapters" / "history" / f"chapter-{number:02d}"
    first = folder / "attempt-01.md"
    second = folder / "attempt-02.md"
    _write(first, initial)
    _write(second, accepted)
    # Hash the stored bytes, rather than the input strings: this keeps the fixture
    # valid on platforms whose text mode writes different line endings.
    digest = hashlib.sha256(second.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "book-genesis.chapter-history/v1",
        "chapter": number,
        "accepted": {
            "attempt_id": f"fixture-{number}-02",
            "sequence": 2,
            "status": "accepted",
            "draft_path": second.relative_to(project).as_posix(),
            "verdict_path": "",
            "sha256": digest,
        },
        "attempts": [
            {
                "attempt_id": f"fixture-{number}-01",
                "sequence": 1,
                "status": "rejected",
                "draft_path": first.relative_to(project).as_posix(),
                "verdict_path": "",
                "sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
            },
            {
                "attempt_id": f"fixture-{number}-02",
                "sequence": 2,
                "status": "accepted",
                "draft_path": second.relative_to(project).as_posix(),
                "verdict_path": "",
                "sha256": digest,
            },
        ],
    }
    _write(folder / "manifest.json", json.dumps(manifest, indent=2) + "\n")


def build(output: Path, source: Path) -> Path:
    sys.path.insert(0, str(source))
    from runner.review import build_review

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="book-genesis-reader-demo-") as temporary:
        return _build_fixture(output, Path(temporary), build_review)


def _build_fixture(output: Path, project: Path, build_review) -> Path:
    _write(project / "PROJECT_STATE.yaml", _state())
    _write(
        project / "RUN_REPORT.md",
        "# Scripted interface sample\n\n"
        "This report is fixture content created by `build_reader_demo.py`. "
        "No provider was called, no manuscript was generated, and no human reader evaluated this sample.\n",
    )
    _write(
        project / "artifacts" / "08-adversarial-audit.md",
        "# Scripted interface sample — provenance\n\n"
        "This page is deterministic fixture data for demonstrating local chapter navigation, version history, "
        "differences, and an audit-blocked state. It is not a model-generated manuscript, an audit result, "
        "a Genesis Score, or evidence of human reader response.\n\n"
        "audit_status: revise\n",
    )
    for number, (initial, accepted) in CHAPTERS.items():
        _write(project / "manuscript" / "chapters" / f"chapter-{number:02d}.md", accepted)
        _history(project, number, initial, accepted)

    generated = build_review(project)
    destination = output / "index.html"
    shutil.copyfile(generated, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic Book Genesis reader sample.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "examples" / "reader-demo")
    parser.add_argument("--source", default="", help="Repository checkout containing runner/ (preparation only).")
    args = parser.parse_args()
    page = build(args.output.resolve(), _source_root(args.source))
    print(page.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
