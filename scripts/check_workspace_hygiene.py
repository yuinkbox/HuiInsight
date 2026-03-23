# -*- coding: utf-8 -*-
"""Workspace hygiene checker for repository root.

This script validates root-level file hygiene rules:
1) Temporary Python scripts should be under scripts/temp/.
2) AI conversation logs should be under docs/ai_conversations/.
3) One-off scripts/text files must not be created directly in repo root.

Exit code:
- 0: no violations
- 1: violations found
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import fnmatch
import sys


@dataclass(frozen=True)
class Rule:
    """A root-level file hygiene rule."""

    pattern: str
    reason: str
    expected_location: str


RULES: tuple[Rule, ...] = (
    Rule("fix_*.py", "Temporary fix script", "scripts/temp/"),
    Rule("check_*.py", "Temporary check script", "scripts/temp/"),
    Rule("MESSAGE_*", "Conversation/log artifact", "docs/ai_conversations/"),
    Rule("QUICK_*", "Conversation/log artifact", "docs/ai_conversations/"),
    Rule("FINAL_*", "Conversation/log artifact", "docs/ai_conversations/"),
    Rule("RESPONSE_*", "Conversation/log artifact", "docs/ai_conversations/"),
)


@dataclass(frozen=True)
class Violation:
    """A file that violates root-level hygiene rules."""

    filename: str
    reason: str
    expected_location: str


def _iter_root_files(repo_root: Path) -> Iterable[Path]:
    """Yield only direct child files of repository root."""
    for path in repo_root.iterdir():
        if path.is_file():
            yield path


def _match_rule(filename: str) -> Rule | None:
    """Return the first matched rule for filename, else None."""
    for rule in RULES:
        if fnmatch.fnmatch(filename, rule.pattern):
            return rule
    return None


def collect_violations(repo_root: Path) -> list[Violation]:
    """Collect root-level violations under the given repository root."""
    violations: list[Violation] = []

    for path in _iter_root_files(repo_root):
        matched_rule = _match_rule(path.name)
        if matched_rule is None:
            continue
        violations.append(
            Violation(
                filename=path.name,
                reason=matched_rule.reason,
                expected_location=matched_rule.expected_location,
            )
        )

    violations.sort(key=lambda item: item.filename.lower())
    return violations


def main() -> int:
    """Run workspace hygiene checks for repository root."""
    repo_root = Path(__file__).resolve().parent.parent
    violations = collect_violations(repo_root)

    if not violations:
        print("[PASS] Workspace hygiene check passed: no root-level temp artifacts found.")
        return 0

    print("[FAIL] Workspace hygiene violations found in repository root:\n")
    for index, violation in enumerate(violations, start=1):
        print(f"{index}. {violation.filename}")
        print(f"   - Reason: {violation.reason}")
        print(f"   - Move to: {violation.expected_location}")

    print(f"\nTotal violations: {len(violations)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
