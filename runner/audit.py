"""Strict machine-readable gate for the adversarial audit artifact."""
from __future__ import annotations

import re

_STATUS = re.compile(r"^audit_status:[ \t]*([^\r\n]*)$", re.IGNORECASE | re.MULTILINE)
_LEGACY_MAJOR = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?"
    r"(?:(?:veredito(?:[ \t]+final)?|(?:final[ \t]+)?verdict|audit verdict)[ \t]*:[ \t]*(?:\*\*)?)?"
    r"(?:major rewrite|reescrita maior)(?:\*\*)?(?=[ \t.!:\r\n]|$)",
    re.IGNORECASE | re.MULTILINE,
)


def audit_status(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = _STATUS.findall(text)
    if len(matches) == 1:
        status = matches[0].strip().lower()
        if status in {"pass", "revise", "major_rewrite"}:
            if status != "major_rewrite" and _LEGACY_MAJOR.search(text):
                raise ValueError("audit_status conflicts with an explicit MAJOR REWRITE verdict")
            return status
    if not matches and _LEGACY_MAJOR.search(text):
        return "major_rewrite"
    raise ValueError("audit artifact must contain exactly one standalone `audit_status: pass|revise|major_rewrite` line")
