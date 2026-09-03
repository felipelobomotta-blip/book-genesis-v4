"""The blind reader.

``judge_chapter`` sends a chapter to a model that has seen nothing else about the
book: no outline, no foundation, no writer notes. The model answers as a reader
(turn the page? where did you stop? what stays with you?) and, when given an
earlier draft or a published anchor, compares. There is no numeric score here on
purpose: comparisons are what a model does reliably; absolute grades are not.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional, Union

from runner.adapters import Adapter

REPO_ROOT = Path(__file__).resolve().parents[1]
JUDGE_TEMPLATE = REPO_ROOT / "agents" / "book-judge.md"

KNOWN_FLAGS = ("hook", "dialogue", "pacing", "ai_pattern", "exposition", "voice", "continuity")


@dataclass(frozen=True)
class Verdict:
    turn_page: bool
    stopped_at: str
    remember: List[str]
    flags: List[str]
    vs_previous: str
    vs_anchor: str
    raw: str


def judge_chapter(
    prose: str,
    previous_tail: str,
    genre: str,
    adapter: Adapter,
    model: str = "",
    *,
    previous_draft: Optional[str] = None,
    anchor: Optional[str] = None,
    reader: str = "",
) -> Verdict:
    prompt = build_judge_prompt(
        prose=prose,
        previous_tail=previous_tail,
        genre=genre,
        previous_draft=previous_draft,
        anchor=anchor,
        reader=reader,
    )
    response = adapter.complete(prompt, model=model)
    return parse_verdict(response)


def build_judge_prompt(
    *,
    prose: str,
    previous_tail: str,
    genre: str,
    previous_draft: Optional[str] = None,
    anchor: Optional[str] = None,
    reader: str = "",
) -> str:
    template = _strip_frontmatter(JUDGE_TEMPLATE.read_text(encoding="utf-8"))
    tail = previous_tail.strip() or "(This is the first chapter. Nothing came before it.)"
    comparison = ""
    if previous_draft:
        comparison += (
            "### An earlier draft of the same chapter\n\n"
            "Read this only after the chapter above. Then answer `vs_previous`: is the chapter above "
            "better, worse, or the same as this draft, for you as a reader, not as an editor?\n\n"
            f"{previous_draft.strip()}\n\n"
        )
    if anchor:
        comparison += (
            "### A published chapter in this genre (anchor)\n\n"
            "Answer `vs_anchor`: is the chapter above closer to this or farther from it, in how it holds "
            "your attention? Do not answer which is better written.\n\n"
            f"{anchor.strip()}\n\n"
        )
    if not comparison:
        comparison = "(No earlier draft and no anchor were given: answer `vs_previous: none` and `vs_anchor: none`.)\n"

    return (
        template.replace("{{genre}}", genre.strip() or "general fiction")
        .replace("{{reader}}", reader.strip() or "a general adult reader")
        .replace("{{previous_tail}}", tail)
        .replace("{{prose}}", prose.strip())
        .replace("{{comparison_section}}", comparison.rstrip())
    )


def parse_verdict(text: str) -> Verdict:
    block = _extract_block(text)
    data = _parse_flat_yaml(block)
    if "turn_page" not in data:
        raise ValueError("verdict block has no turn_page")
    turn_page = _as_bool(_as_text(data["turn_page"]))
    return Verdict(
        turn_page=turn_page,
        stopped_at=_as_text(data.get("stopped_at", "none")) or "none",
        remember=_as_list(data.get("remember", [])),
        flags=[flag.lower() for flag in _as_list(data.get("flags", []))],
        vs_previous=(_as_text(data.get("vs_previous", "none")) or "none").lower(),
        vs_anchor=(_as_text(data.get("vs_anchor", "none")) or "none").lower(),
        raw=text,
    )


_FENCE = re.compile(r"```[a-zA-Z]*[ \t]*\r?\n(.*?)```", re.DOTALL)


def _extract_block(text: str) -> str:
    for match in _FENCE.finditer(text):
        body = match.group(1)
        if "turn_page:" in body:
            return body
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("turn_page:"):
            return "\n".join(lines[index:])
    raise ValueError("no verdict block (turn_page:) found in judge response")


def _parse_flat_yaml(block: str) -> Dict[str, Union[str, List[str]]]:
    data: Dict[str, Union[str, List[str]]] = {}
    current_list: Optional[str] = None
    for raw in block.splitlines():
        line = _strip_comment(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_list is None:
                raise ValueError(f"list item without a key: {stripped}")
            data[current_list].append(_unquote(stripped[2:].strip()))  # type: ignore[union-attr]
            continue
        if ":" not in stripped:
            raise ValueError(f"unparseable verdict line: {stripped}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list = key
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [_unquote(item.strip()) for item in inner.split(",") if item.strip()] if inner else []
            current_list = None
        else:
            data[key] = _unquote(value)
            current_list = None
    return data


def _strip_comment(line: str) -> str:
    quote = ""
    for index, character in enumerate(line):
        if quote:
            if character == quote:
                quote = ""
            continue
        if character in ("'", '"'):
            quote = character
            continue
        if character == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _as_text(value: Union[str, List[str]]) -> str:
    if isinstance(value, list):
        return ", ".join(value)
    return value.strip()


def _as_list(value: Union[str, List[str]]) -> List[str]:
    if isinstance(value, list):
        return [item for item in value if item and item.lower() != "none"]
    text = value.strip()
    if not text or text.lower() == "none":
        return []
    return [text]


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("yes", "true", "y"):
        return True
    if normalized in ("no", "false", "n"):
        return False
    raise ValueError(f"turn_page must be yes or no, got {value!r}")


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\r\n")
    return text
