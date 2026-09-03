"""The reader panel: several blind judges, different families and personas, one verdict.

It stands where a human checkpoint used to be (ADR 0002). Each member reads the prose
exactly as the single judge does, with its own persona; the panel aggregates by majority.
A panel of models is a cheaper and less biased signal than self-grading. It is still not
a room full of human readers, and the documentation says so.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from typing import List, Optional, Sequence

from runner.adapters import Adapter, AdapterError
from runner.judge import Verdict, judge_chapter


@dataclass
class PanelMember:
    adapter: Adapter
    model: str
    persona: str

    @property
    def label(self) -> str:
        name = getattr(self.adapter, "name", "adapter")
        return f"{name} {self.model}".strip()


class PanelJudge:
    def __init__(self, members: Sequence[PanelMember]) -> None:
        if not members:
            raise ValueError("a panel needs at least one member")
        self.members: List[PanelMember] = list(members)
        self.last_verdicts: List[Verdict] = []
        self.last_failures: List[str] = []

    @property
    def label(self) -> str:
        seats = ", ".join(f"{member.label} as {member.persona}" for member in self.members)
        return f"panel of {len(self.members)} ({seats})"

    def judge(
        self,
        prose: str,
        previous_tail: str,
        genre: str,
        *,
        previous_draft: Optional[str] = None,
        reader: str = "",
    ) -> Verdict:
        verdicts: List[Verdict] = []
        labels: List[str] = []
        failures: List[str] = []
        for member in self.members:
            try:
                verdict = judge_chapter(
                    prose,
                    previous_tail,
                    genre,
                    member.adapter,
                    member.model,
                    previous_draft=previous_draft,
                    reader=member.persona,
                )
            except (AdapterError, ValueError) as exc:
                failures.append(f"{member.persona} ({member.label}): {exc}")
                continue
            verdicts.append(verdict)
            labels.append(f"{member.persona} ({member.label})")
        self.last_verdicts = verdicts
        self.last_failures = failures
        if not verdicts:
            raise AdapterError("every panel member failed: " + "; ".join(failures))
        return aggregate(verdicts, labels=labels, failures=failures)


def aggregate(
    verdicts: Sequence[Verdict],
    *,
    labels: Optional[Sequence[str]] = None,
    failures: Optional[Sequence[str]] = None,
) -> Verdict:
    """Majority rules. Flags need two citations in a panel of three or more, one otherwise."""
    if not verdicts:
        raise ValueError("cannot aggregate an empty panel")
    count = len(verdicts)
    yes = sum(1 for verdict in verdicts if verdict.turn_page)
    turn_page = yes * 2 > count

    threshold = 2 if count >= 3 else 1
    flag_counts: Counter = Counter()
    first_seen: dict = {}
    for index, verdict in enumerate(verdicts):
        for flag in dict.fromkeys(verdict.flags):
            flag_counts[flag] += 1
            first_seen.setdefault(flag, index)
    flags = [
        flag
        for flag, number in sorted(flag_counts.items(), key=lambda item: (-item[1], first_seen[item[0]]))
        if number >= threshold
    ]

    stop_counts: Counter = Counter()
    stop_first: dict = {}
    for index, verdict in enumerate(verdicts):
        stop = verdict.stopped_at.strip()
        if stop and stop.lower() != "none":
            stop_counts[stop] += 1
            stop_first.setdefault(stop, index)
    stopped_at = "none"
    if stop_counts:
        stopped_at = sorted(stop_counts.items(), key=lambda item: (-item[1], stop_first[item[0]]))[0][0]

    remember = list(dict.fromkeys(item for verdict in verdicts for item in verdict.remember))
    vs_previous = _majority([verdict.vs_previous for verdict in verdicts])
    vs_anchor = _majority([verdict.vs_anchor for verdict in verdicts])

    raw = _render(verdicts, labels or [], failures or [], turn_page, stopped_at, remember, flags, vs_previous, vs_anchor, yes)
    return Verdict(
        turn_page=turn_page,
        stopped_at=stopped_at,
        remember=remember,
        flags=flags,
        vs_previous=vs_previous,
        vs_anchor=vs_anchor,
        raw=raw,
    )


def _majority(values: Sequence[str]) -> str:
    votes = Counter(value for value in values if value and value != "none")
    if not votes:
        return "none"
    ranked = votes.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "same"
    return ranked[0][0]


def _render(
    verdicts: Sequence[Verdict],
    labels: Sequence[str],
    failures: Sequence[str],
    turn_page: bool,
    stopped_at: str,
    remember: Sequence[str],
    flags: Sequence[str],
    vs_previous: str,
    vs_anchor: str,
    yes: int,
) -> str:
    lines = ["# Reader panel", ""]
    for index, verdict in enumerate(verdicts):
        label = labels[index] if index < len(labels) else f"reader {index + 1}"
        lines += [f"## {label}", "", verdict.raw.strip(), ""]
    for failure in failures:
        lines += [f"## failed: {failure}", ""]
    remember_yaml = "\n".join(f"  - {json.dumps(item, ensure_ascii=False)}" for item in remember) or "  []"
    stopped_yaml = "none" if stopped_at == "none" else json.dumps(stopped_at, ensure_ascii=False)
    lines += [
        f"## Aggregate ({yes} of {len(verdicts)} would turn the page)",
        "",
        "```yaml",
        f"turn_page: {'yes' if turn_page else 'no'}",
        f"stopped_at: {stopped_yaml}",
        "remember:" if remember else "remember: []",
    ]
    if remember:
        lines.append(remember_yaml)
    lines += [
        "flags: [" + ", ".join(flags) + "]",
        f"vs_previous: {vs_previous}",
        f"vs_anchor: {vs_anchor}",
        "```",
        "",
    ]
    return "\n".join(lines)
