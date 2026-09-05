"""The chapter brief: the one document the writer sees.

Assembled deterministically from project files, never by a model: the chapter's
own section of the outline, the story engine, the characters, the tail of the
previous chapter, and the genre constants. Everything else stays out of the
writer's context on purpose (ADR 0001, decision 7).
"""

from __future__ import annotations

from pathlib import Path
import re

from runner.constants import load_genre_profile
from runner.filesystem import load_state_summary

TAIL_WORDS = 300
OUTLINE_PATH = "artifacts/05-outline.md"
ALWAYS_INCLUDE = (
    ("artifacts/02-story-engine.md", "Story engine"),
    ("artifacts/03-characters.md", "Characters"),
)
FIRST_CHAPTER_NOTE = "(This is the first chapter. Nothing came before it.)"

_HEADING = re.compile(r"^(#{1,6})\s*(.*?)\s*$")
_WORD = re.compile(r"\S+")

# A chapter marker is a heading (`## Chapter 3: Title`) or, because real architecture runs
# produced it, a bold line (`**Capítulo 3 — Título**`). English and Portuguese.
CHAPTER_MARK = re.compile(
    r"^\s*(?:(?P<hashes>#{1,6})\s*|\*\*\s*)(?:chapter|cap[ií]tulo|cap\.?)\s*0*(?P<number>\d+)\b",
    re.IGNORECASE,
)


def build_chapter_brief(project: Path, chapter: int, *, write: bool = True) -> str:
    summary = load_state_summary(project)
    genre = summary.get("genre", "")
    profile = load_genre_profile(genre)

    outline_path = project / OUTLINE_PATH
    if not outline_path.exists():
        raise ValueError(f"outline not found at {outline_path}")
    section = extract_chapter_section(outline_path.read_text(encoding="utf-8"), chapter)

    previous_tail = ""
    if chapter > 1:
        previous = project / "manuscript" / "chapters" / f"chapter-{chapter - 1:02d}.md"
        if previous.exists():
            previous_tail = tail_words(previous.read_text(encoding="utf-8"), TAIL_WORDS)

    parts = [
        f"# Brief: Chapter {chapter}",
        "",
        "## Constants",
        "",
        f"- Genre profile: {profile.key} (declared genre: {genre or 'unspecified'})",
        f"- Target length: {profile.words_per_chapter_min}-{profile.words_per_chapter_max} words, "
        "unless the outline section below states its own target.",
        f"- Dialogue share: {profile.dialogue_min_pct}-{profile.dialogue_max_pct}% of the chapter.",
        "",
        "## This chapter in the outline",
        "",
        section.strip(),
        "",
    ]
    for relative, heading in ALWAYS_INCLUDE:
        path = project / relative
        if path.exists():
            parts += [f"## {heading}", "", path.read_text(encoding="utf-8").strip(), ""]
    notes = project / "work" / "author-notes.md"
    if notes.exists() and notes.read_text(encoding="utf-8").strip():
        parts += [
            "## Author notes",
            "",
            "The author asked for these while reading earlier results. They override the defaults above.",
            "",
            notes.read_text(encoding="utf-8").strip(),
            "",
        ]
    parts += [
        "## Where the previous chapter left the reader",
        "",
        previous_tail or FIRST_CHAPTER_NOTE,
        "",
    ]
    brief = "\n".join(parts)

    if write:
        briefs_dir = project / "briefs"
        briefs_dir.mkdir(parents=True, exist_ok=True)
        (briefs_dir / f"chapter-{chapter:02d}.md").write_text(brief, encoding="utf-8")
    return brief


def extract_chapter_section(outline: str, chapter: int) -> str:
    """Return the marker line + body of ``chapter`` from a Markdown outline.

    Accepts ``Chapter N`` / ``Capítulo N`` / ``Cap. N`` as a heading at any level or as a
    bold line. The section ends at the next chapter marker, or at the next heading of the
    same or a higher level (any heading, when the marker was a bold line).
    """
    lines = outline.splitlines()
    start = -1
    level = 0
    for index, line in enumerate(lines):
        match = CHAPTER_MARK.match(line)
        if match and int(match.group("number")) == chapter:
            start = index
            level = len(match.group("hashes") or "")
            break
    if start == -1:
        raise ValueError(f"chapter {chapter} not found in outline")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if CHAPTER_MARK.match(line):
            end = index
            break
        heading = _HEADING.match(line)
        if heading and (level == 0 or len(heading.group(1)) <= level):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def tail_words(text: str, count: int) -> str:
    """Last ``count`` words of ``text`` with the original line breaks preserved."""
    spans = list(_WORD.finditer(text))
    if len(spans) <= count:
        return text.strip()
    return text[spans[-count].start() :].strip()
