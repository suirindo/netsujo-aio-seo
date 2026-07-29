#!/usr/bin/env python3
"""Run deterministic policy regressions for visibility-map skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "plugins/netsujo-aio/skills"
CASES_PATH = (
    SKILLS_DIR
    / "goal-backcast-visibility-map"
    / "evals"
    / "eval-cases.json"
)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def validate_case(case: Any, known_ids: set[str]) -> list[str]:
    if not isinstance(case, dict):
        return ["case must be an object"]
    case_id = case.get("id", "<missing>")
    errors: list[str] = []
    if case_id in known_ids:
        errors.append(f"{case_id}: duplicate ID")
    known_ids.add(case_id)
    for key in ("scenario", "expectedDecision"):
        if not isinstance(case.get(key), str) or not case[key].strip():
            errors.append(f"{case_id}: {key} must be a non-empty string")
    owners = case.get("ownerSkills")
    tokens = case.get("requiredPolicyTokens")
    if not isinstance(owners, list) or not owners:
        errors.append(f"{case_id}: ownerSkills must be a non-empty array")
        owners = []
    if not isinstance(tokens, list) or not tokens:
        errors.append(
            f"{case_id}: requiredPolicyTokens must be a non-empty array"
        )
        tokens = []

    owner_texts: list[str] = []
    for owner in owners:
        path = SKILLS_DIR / owner / "SKILL.md"
        if not path.is_file():
            errors.append(f"{case_id}: missing owner skill {owner}")
            continue
        owner_texts.append(path.read_text(encoding="utf-8"))
    combined = normalize("\n".join(owner_texts))
    for token in tokens:
        if not isinstance(token, str) or len(token.strip()) < 8:
            errors.append(f"{case_id}: policy tokens must be specific strings")
        elif normalize(token) not in combined:
            errors.append(f"{case_id}: missing policy token {token!r}")
    return errors


def main() -> int:
    try:
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Eval setup failed: {error}")
        return 1
    if not isinstance(cases, list):
        print("Eval setup failed: eval-cases.json must be an array")
        return 1

    errors: list[str] = []
    known_ids: set[str] = set()
    for case in cases:
        case_errors = validate_case(case, known_ids)
        errors.extend(case_errors)
        case_id = case.get("id", "<missing>") if isinstance(case, dict) else "?"
        print(f"{'FAIL' if case_errors else 'PASS'} {case_id}")

    expected_ids = {f"E{index:02d}" for index in range(1, 19)}
    if known_ids != expected_ids or len(cases) != 18:
        errors.append("suite must contain exactly E01 through E18")
    if errors:
        print(f"\nPolicy regression failed ({len(errors)} errors):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nPolicy regression passed: 18/18.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
