#!/usr/bin/env python3
"""Strict, dependency-free validation for Netsujo visibility data contracts."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


CONTRACT_DIR = Path(
    "plugins/netsujo-aio/skills/goal-backcast-visibility-map"
)
FIXTURE_DIR = CONTRACT_DIR / "evals/fixtures"
SCHEMA_DIR = CONTRACT_DIR / "schemas"
EXPECTED_PLUGIN_VERSION = "0.5.0"
EXPECTED_SKILL_COUNT = 21

SEARCH_STATUSES = {
    "SEARCH_OWNED",
    "SEARCH_VISIBLE",
    "SEARCH_EMERGING",
    "SEARCH_CTR_GAP",
    "SEARCH_PAGE_MISMATCH",
    "SEARCH_CONTENT_GAP",
    "SEARCH_UNMEASURED",
}
AI_STATUSES = {
    "AI_CITED_STABLE",
    "AI_CITED_VOLATILE",
    "AI_MENTION_NO_CITATION",
    "AI_NOT_CITED",
    "AI_ANSWER_READY",
    "AI_CONTENT_PARTIAL",
    "AI_CONTENT_GAP",
    "AI_FACT_CONFLICT",
    "AI_UNMEASURED",
}
SAFE_REFRESH_ERRORS = {
    "upstream_timeout",
    "upstream_rate_limited",
    "upstream_server_error",
    "upstream_invalid_response",
    "refresh_incomplete",
}
FORBIDDEN_AI_KEY_FRAGMENTS = {
    "answer",
    "body",
    "prompt",
    "cookie",
    "apikey",
    "api_key",
    "token",
    "secret",
    "authorization",
}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_datetime(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return "T" in value


def _is_http_url(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _check_exact_keys(
    value: Any,
    required: set[str],
    allowed: set[str],
    path: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path}: must be an object"]
    errors = [
        f"{path}: missing required key {key}"
        for key in sorted(required - set(value))
    ]
    errors.extend(
        f"{path}: unsupported key {key}"
        for key in sorted(set(value) - allowed)
    )
    return errors


def _check_version(
    value: dict[str, Any], contract: str, path: str
) -> list[str]:
    errors: list[str] = []
    if value.get("contract") != contract:
        errors.append(f"{path}.contract: unsupported contract")
    if value.get("schemaVersion") != 1:
        errors.append(f"{path}.schemaVersion: unsupported version")
    return errors


def _find_forbidden_ai_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z_]", "", key.lower())
            if any(fragment in normalized for fragment in FORBIDDEN_AI_KEY_FRAGMENTS):
                errors.append(f"{path}.{key}: forbidden AI snapshot field")
            errors.extend(_find_forbidden_ai_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_forbidden_ai_keys(child, f"{path}[{index}]"))
    return errors


def validate_visibility_registry(value: Any) -> list[str]:
    required = {
        "contract",
        "schemaVersion",
        "registryVersion",
        "generatedAt",
        "goals",
        "targets",
    }
    errors = _check_exact_keys(value, required, required, "$")
    if not isinstance(value, dict):
        return errors
    errors.extend(_check_version(value, "visibility-targets/v1", "$"))
    if not _is_non_empty_string(value.get("registryVersion")):
        errors.append("$.registryVersion: must be a non-empty string")
    if not _is_datetime(value.get("generatedAt")):
        errors.append("$.generatedAt: must be an ISO date-time")

    goals = value.get("goals")
    targets = value.get("targets")
    if not isinstance(goals, list) or not goals:
        errors.append("$.goals: must be a non-empty array")
        goals = []
    if not isinstance(targets, list):
        errors.append("$.targets: must be an array")
        targets = []

    goal_required = {
        "id",
        "siteId",
        "label",
        "actor",
        "decision",
        "conversionIds",
    }
    goal_ids: set[str] = set()
    goal_sites: dict[str, str] = {}
    for index, goal in enumerate(goals):
        path = f"$.goals[{index}]"
        errors.extend(_check_exact_keys(goal, goal_required, goal_required, path))
        if not isinstance(goal, dict):
            continue
        goal_id = goal.get("id")
        if not _is_non_empty_string(goal_id):
            errors.append(f"{path}.id: must be a non-empty string")
        elif goal_id in goal_ids:
            errors.append(f"{path}.id: duplicate goal ID {goal_id}")
        else:
            goal_ids.add(goal_id)
            goal_sites[goal_id] = goal.get("siteId")
        for key in ("siteId", "label", "actor", "decision"):
            if not _is_non_empty_string(goal.get(key)):
                errors.append(f"{path}.{key}: must be a non-empty string")
        conversions = goal.get("conversionIds")
        if (
            not isinstance(conversions, list)
            or not conversions
            or not all(_is_non_empty_string(item) for item in conversions)
            or len(set(conversions)) != len(conversions)
        ):
            errors.append(
                f"{path}.conversionIds: must contain unique conversion references"
            )

    target_required = {
        "id",
        "siteId",
        "kind",
        "clusterId",
        "goalId",
        "text",
        "variants",
        "locale",
        "branded",
        "persona",
        "intent",
        "funnelStage",
        "priority",
        "targetUrl",
        "gapReason",
        "evidenceUrls",
        "ctaEventNames",
        "owner",
        "active",
        "createdAt",
        "updatedAt",
    }
    target_ids: set[str] = set()
    for index, target in enumerate(targets):
        path = f"$.targets[{index}]"
        errors.extend(
            _check_exact_keys(target, target_required, target_required, path)
        )
        if not isinstance(target, dict):
            continue
        target_id = target.get("id")
        if not _is_non_empty_string(target_id):
            errors.append(f"{path}.id: must be a non-empty string")
        elif target_id in target_ids:
            errors.append(f"{path}.id: duplicate target ID {target_id}")
        else:
            target_ids.add(target_id)
        goal_id = target.get("goalId")
        if goal_id not in goal_ids:
            errors.append(f"{path}.goalId: orphan goal reference {goal_id}")
        elif target.get("siteId") != goal_sites.get(goal_id):
            errors.append(f"{path}.siteId: does not match referenced goal")
        if target.get("kind") not in {"search_keyword", "ai_question"}:
            errors.append(f"{path}.kind: unsupported target kind")
        for key in (
            "siteId",
            "clusterId",
            "text",
            "locale",
            "persona",
            "intent",
            "funnelStage",
            "owner",
        ):
            if not _is_non_empty_string(target.get(key)):
                errors.append(f"{path}.{key}: must be a non-empty string")
        if target.get("priority") not in {"P0", "P1", "P2"}:
            errors.append(f"{path}.priority: unsupported priority")
        if not isinstance(target.get("branded"), bool):
            errors.append(f"{path}.branded: must be boolean")
        if not isinstance(target.get("active"), bool):
            errors.append(f"{path}.active: must be boolean")
        variants = target.get("variants")
        if (
            not isinstance(variants, list)
            or not all(_is_non_empty_string(item) for item in variants)
            or len(set(variants)) != len(variants)
            or target.get("text") in variants
        ):
            errors.append(f"{path}.variants: must contain unique wording variants")
        target_url = target.get("targetUrl")
        gap_reason = target.get("gapReason")
        if target_url is not None and not _is_http_url(target_url):
            errors.append(f"{path}.targetUrl: must be null or an HTTP(S) URL")
        if gap_reason is not None and not _is_non_empty_string(gap_reason):
            errors.append(f"{path}.gapReason: must be null or a non-empty string")
        if target_url is None and gap_reason is None:
            errors.append(f"{path}: targetUrl or gapReason is required")
        for key in ("evidenceUrls", "ctaEventNames"):
            items = target.get(key)
            if not isinstance(items, list) or not all(
                _is_non_empty_string(item) for item in items
            ):
                errors.append(f"{path}.{key}: must be a string array")
        if isinstance(target.get("evidenceUrls"), list) and not all(
            _is_http_url(item) for item in target["evidenceUrls"]
        ):
            errors.append(f"{path}.evidenceUrls: must contain HTTP(S) URLs")
        for key in ("createdAt", "updatedAt"):
            if not _is_datetime(target.get(key)):
                errors.append(f"{path}.{key}: must be an ISO date-time")
    return errors


def validate_ai_snapshot(value: Any) -> list[str]:
    required = {
        "contract",
        "schemaVersion",
        "snapshotId",
        "siteId",
        "observedAt",
        "status",
        "observations",
        "providerFailures",
    }
    errors = _check_exact_keys(value, required, required, "$")
    if not isinstance(value, dict):
        return errors
    errors.extend(_check_version(value, "ai-citation-snapshot/v1", "$"))
    errors.extend(_find_forbidden_ai_keys(value))
    for key in ("snapshotId", "siteId"):
        if not _is_non_empty_string(value.get(key)):
            errors.append(f"$.{key}: must be a non-empty string")
    if not _is_datetime(value.get("observedAt")):
        errors.append("$.observedAt: must be an ISO date-time")
    if value.get("status") not in {"success", "partial", "error"}:
        errors.append("$.status: unsupported snapshot status")
    failures = value.get("providerFailures")
    if not isinstance(failures, list):
        errors.append("$.providerFailures: must be an array")
        failures = []
    for index, failure in enumerate(failures):
        path = f"$.providerFailures[{index}]"
        failure_keys = {"engine", "code"}
        errors.extend(
            _check_exact_keys(failure, failure_keys, failure_keys, path)
        )
        if not isinstance(failure, dict):
            continue
        if not _is_non_empty_string(failure.get("engine")):
            errors.append(f"{path}.engine: must be a non-empty string")
        if failure.get("code") not in {
            "timeout",
            "rate_limited",
            "upstream_5xx",
            "invalid_payload",
            "network",
        }:
            errors.append(f"{path}.code: unsupported provider failure")

    observations = value.get("observations")
    if not isinstance(observations, list):
        errors.append("$.observations: must be an array")
        return errors
    expected_status = (
        "success"
        if not failures
        else "error"
        if not observations
        else "partial"
    )
    if value.get("status") != expected_status:
        errors.append("$.status: does not match observations/providerFailures")
    observation_required = {
        "targetId",
        "observedAt",
        "engine",
        "model",
        "locale",
        "variantId",
        "runCount",
        "successCount",
        "ownMentionCount",
        "ownCitationCount",
        "ownCitationUrls",
        "competitorDomains",
        "stability",
        "factCheck",
        "snapshotRef",
    }
    for index, observation in enumerate(observations):
        path = f"$.observations[{index}]"
        errors.extend(
            _check_exact_keys(
                observation,
                observation_required,
                observation_required,
                path,
            )
        )
        if not isinstance(observation, dict):
            continue
        for key in (
            "targetId",
            "engine",
            "locale",
            "variantId",
            "snapshotRef",
        ):
            if not _is_non_empty_string(observation.get(key)):
                errors.append(f"{path}.{key}: must be a non-empty string")
        if (
            not _is_datetime(observation.get("observedAt"))
            or observation.get("observedAt") != value.get("observedAt")
        ):
            errors.append(f"{path}.observedAt: must match snapshot observedAt")
        model = observation.get("model")
        if model is not None and not _is_non_empty_string(model):
            errors.append(f"{path}.model: must be null or a non-empty string")
        if observation.get("snapshotRef") != value.get("snapshotId"):
            errors.append(f"{path}.snapshotRef: snapshot provenance mismatch")

        count_keys = (
            "runCount",
            "successCount",
            "ownMentionCount",
            "ownCitationCount",
        )
        for key in count_keys:
            if not _is_int(observation.get(key)) or observation[key] < 0:
                errors.append(f"{path}.{key}: must be a non-negative integer")
        if all(_is_int(observation.get(key)) for key in count_keys):
            runs = observation["runCount"]
            success = observation["successCount"]
            mentions = observation["ownMentionCount"]
            citations = observation["ownCitationCount"]
            if not (citations <= mentions <= success <= runs):
                errors.append(
                    f"{path}: counts must satisfy citation <= mention <= success <= run"
                )
            if observation.get("stability") == "stable" and (
                runs < 3 or success < 3
            ):
                errors.append(
                    f"{path}.stability: stable requires at least three successful same-condition runs"
                )
            expected_stability = (
                "unmeasured"
                if success == 0
                else "not_cited"
                if citations == 0
                else "stable"
                if success >= 3 and citations == success and success == runs
                else "volatile"
            )
            if observation.get("stability") != expected_stability:
                errors.append(
                    f"{path}.stability: does not match the observation counts"
                )
        if observation.get("stability") not in {
            "stable",
            "volatile",
            "not_cited",
            "unmeasured",
        }:
            errors.append(f"{path}.stability: unsupported value")
        if observation.get("factCheck") not in {
            "pass",
            "warn",
            "fail",
            "unmeasured",
        }:
            errors.append(f"{path}.factCheck: unsupported value")
        for key in (
            "ownCitationUrls",
            "competitorDomains",
        ):
            items = observation.get(key)
            if not isinstance(items, list) or not all(
                _is_non_empty_string(item) for item in items
            ):
                errors.append(f"{path}.{key}: must be a string array")
        if isinstance(observation.get("ownCitationUrls"), list) and not all(
            _is_http_url(item) for item in observation["ownCitationUrls"]
        ):
            errors.append(f"{path}.ownCitationUrls: must contain HTTP(S) URLs")
    return errors


def validate_community_stats_snapshot(value: Any) -> list[str]:
    required = {
        "contract",
        "schemaVersion",
        "snapshotId",
        "source",
        "sourceEvidenceRef",
        "fetchedAt",
        "memberCount",
        "eventCount",
        "eventCountRuleVersion",
        "eventBreakdown",
        "pageCount",
        "sourceEventCount",
    }
    errors = _check_exact_keys(value, required, required, "$")
    if not isinstance(value, dict):
        return errors
    errors.extend(_check_version(value, "community-stats-snapshot/v1", "$"))
    for key in ("snapshotId", "source"):
        if not _is_non_empty_string(value.get(key)):
            errors.append(f"$.{key}: must be a non-empty string")
    if not _is_http_url(value.get("sourceEvidenceRef")):
        errors.append("$.sourceEvidenceRef: must be an HTTP(S) URL")
    if not _is_datetime(value.get("fetchedAt")):
        errors.append("$.fetchedAt: must be an ISO date-time")
    for key in ("memberCount", "eventCount", "pageCount", "sourceEventCount"):
        if not _is_int(value.get(key)) or value[key] < 0:
            errors.append(f"$.{key}: must be a non-negative integer")
    if _is_int(value.get("pageCount")) and value["pageCount"] < 1:
        errors.append("$.pageCount: must be at least one")
    if value.get("eventCountRuleVersion") != "connpass-published-events-v1":
        errors.append("$.eventCountRuleVersion: unsupported count rule")

    breakdown = value.get("eventBreakdown")
    breakdown_keys = {
        "completed",
        "cancelled",
        "upcoming",
    }
    errors.extend(
        _check_exact_keys(
            breakdown, breakdown_keys, breakdown_keys, "$.eventBreakdown"
        )
    )
    if isinstance(breakdown, dict):
        for key in breakdown_keys:
            count = breakdown.get(key)
            if not _is_int(count) or count < 0:
                errors.append(
                    f"$.eventBreakdown.{key}: must be a non-negative integer"
                )
        included_keys = ("completed", "cancelled", "upcoming")
        if (
            _is_int(value.get("eventCount"))
            and all(_is_int(breakdown.get(key)) for key in included_keys)
            and value["eventCount"]
            != sum(breakdown[key] for key in included_keys)
        ):
            errors.append(
                "$.eventCount: must equal completed + cancelled + upcoming"
            )

    if (
        _is_int(value.get("eventCount"))
        and _is_int(value.get("sourceEventCount"))
        and value["sourceEventCount"] != value["eventCount"]
    ):
        errors.append("$.sourceEventCount: must equal eventCount")
    return errors


def validate_dashboard_import(value: Any) -> list[str]:
    required = {
        "contract",
        "schemaVersion",
        "siteId",
        "generatedAt",
        "registryVersion",
        "searchIntegration",
        "searchSnapshotId",
        "aiIntegration",
        "aiSnapshotId",
        "rows",
    }
    errors = _check_exact_keys(value, required, required, "$")
    if not isinstance(value, dict):
        return errors
    errors.extend(_check_version(value, "visibility-dashboard-import/v1", "$"))
    for key in ("siteId", "registryVersion"):
        if not _is_non_empty_string(value.get(key)):
            errors.append(f"$.{key}: must be a non-empty string")
    if not _is_datetime(value.get("generatedAt")):
        errors.append("$.generatedAt: must be an ISO date-time")

    search_integration = value.get("searchIntegration")
    if search_integration not in {
        "measured",
        "empty",
        "not_configured",
        "permission_denied",
        "error",
    }:
        errors.append("$.searchIntegration: unsupported value")
    if search_integration in {"measured", "empty"}:
        if not _is_non_empty_string(value.get("searchSnapshotId")):
            errors.append(
                "$.searchSnapshotId: successful GSC import requires provenance"
            )
    elif value.get("searchSnapshotId") is not None:
        errors.append(
            "$.searchSnapshotId: unavailable GSC integration must use null"
        )

    ai_integration = value.get("aiIntegration")
    if ai_integration not in {"measured", "partial", "unmeasured", "error"}:
        errors.append("$.aiIntegration: unsupported value")
    if ai_integration in {"measured", "partial"}:
        if not _is_non_empty_string(value.get("aiSnapshotId")):
            errors.append(
                "$.aiSnapshotId: measured AI integration requires provenance"
            )
    elif value.get("aiSnapshotId") is not None:
        errors.append(
            "$.aiSnapshotId: unavailable AI integration must use null"
        )

    rows = value.get("rows")
    if not isinstance(rows, list):
        errors.append("$.rows: must be an array")
        return errors
    row_required = {
        "targetId",
        "searchStatus",
        "aiStatus",
        "contentReadiness",
        "conversionStatus",
    }
    target_ids: set[str] = set()
    for index, row in enumerate(rows):
        path = f"$.rows[{index}]"
        errors.extend(_check_exact_keys(row, row_required, row_required, path))
        if not isinstance(row, dict):
            continue
        target_id = row.get("targetId")
        if not _is_non_empty_string(target_id):
            errors.append(f"{path}.targetId: must be a non-empty string")
        elif target_id in target_ids:
            errors.append(f"{path}.targetId: duplicate dashboard target")
        else:
            target_ids.add(target_id)
        if row.get("searchStatus") not in SEARCH_STATUSES:
            errors.append(f"{path}.searchStatus: unsupported search status")
        if row.get("aiStatus") not in AI_STATUSES:
            errors.append(f"{path}.aiStatus: unsupported AI status")
        if row.get("contentReadiness") not in {
            "ready",
            "partial",
            "gap",
            "unmeasured",
        }:
            errors.append(f"{path}.contentReadiness: unsupported value")
        if row.get("conversionStatus") not in {
            "connected",
            "unconnected",
            "unmeasured",
        }:
            errors.append(f"{path}.conversionStatus: unsupported value")
    return errors


def _load_json(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"{path}: {error}"]


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    contract_root = root / CONTRACT_DIR
    schemas = sorted((root / SCHEMA_DIR).glob("*.json"))
    if len(schemas) != 4:
        errors.append(f"{SCHEMA_DIR}: expected 4 schemas, found {len(schemas)}")
    for path in schemas:
        schema, load_errors = _load_json(path)
        errors.extend(load_errors)
        if isinstance(schema, dict) and schema.get("additionalProperties") is not False:
            errors.append(f"{path}: top-level contract must be strict")

    fixture_validators: dict[str, Callable[[Any], list[str]]] = {
        "visibility-targets.valid.json": validate_visibility_registry,
        "ai-citation-snapshot.valid.json": validate_ai_snapshot,
        "community-stats-snapshot.valid.json": validate_community_stats_snapshot,
        "visibility-dashboard-import.valid.json": validate_dashboard_import,
    }
    for name, validator in fixture_validators.items():
        path = root / FIXTURE_DIR / name
        fixture, load_errors = _load_json(path)
        errors.extend(load_errors)
        if not load_errors:
            errors.extend(f"{path}: {error}" for error in validator(fixture))

    plugin_manifest, load_errors = _load_json(
        root / "plugins/netsujo-aio/plugin.json"
    )
    errors.extend(load_errors)
    if isinstance(plugin_manifest, dict):
        if plugin_manifest.get("version") != EXPECTED_PLUGIN_VERSION:
            errors.append(
                "plugins/netsujo-aio/plugin.json: version must be "
                f"{EXPECTED_PLUGIN_VERSION}"
            )
        if "21 skills" not in plugin_manifest.get("description", ""):
            errors.append(
                "plugins/netsujo-aio/plugin.json: description must state 21 skills"
            )

    marketplace, load_errors = _load_json(root / ".claude-plugin/marketplace.json")
    errors.extend(load_errors)
    if isinstance(marketplace, dict):
        plugins = marketplace.get("plugins")
        if (
            not isinstance(plugins, list)
            or len(plugins) != 1
            or plugins[0].get("version") != EXPECTED_PLUGIN_VERSION
        ):
            errors.append(
                ".claude-plugin/marketplace.json: plugin version must match "
                f"{EXPECTED_PLUGIN_VERSION}"
            )

    skill_dirs = sorted(
        path
        for path in (root / "plugins/netsujo-aio/skills").iterdir()
        if path.is_dir()
    )
    if len(skill_dirs) != EXPECTED_SKILL_COUNT:
        errors.append(
            "plugins/netsujo-aio/skills: expected "
            f"{EXPECTED_SKILL_COUNT}, found {len(skill_dirs)}"
        )
    for skill_dir in skill_dirs:
        skill_path = skill_dir / "SKILL.md"
        try:
            first_lines = skill_path.read_text(encoding="utf-8").splitlines()[:10]
        except OSError as error:
            errors.append(f"{skill_path}: {error}")
            continue
        if not first_lines or first_lines[0] != "---":
            errors.append(f"{skill_path}: missing YAML frontmatter")
        if not any(line.startswith("name: ") for line in first_lines):
            errors.append(f"{skill_path}: missing name")
        if not any(line.startswith("description: ") for line in first_lines):
            errors.append(f"{skill_path}: missing description")

    eval_path = contract_root / "evals/eval-cases.json"
    eval_cases, load_errors = _load_json(eval_path)
    errors.extend(load_errors)
    if isinstance(eval_cases, list):
        expected_ids = {f"E{index:02d}" for index in range(1, 19)}
        actual_ids = {
            case.get("id") for case in eval_cases if isinstance(case, dict)
        }
        if actual_ids != expected_ids or len(eval_cases) != 18:
            errors.append(f"{eval_path}: must define exactly E01 through E18")

    stale_literal_patterns = {
        "564 current members": re.compile(r"564[^\n]{0,30}member", re.I),
        "155+ current events": re.compile(r"155\\+[^\n]{0,30}event", re.I),
        "614 current members": re.compile(r"614[^\n]{0,30}member", re.I),
        "167 current events": re.compile(r"167[^\n]{0,30}event", re.I),
    }
    scan_paths = [root / "README.md", *[path / "SKILL.md" for path in skill_dirs]]
    for path in scan_paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for label, pattern in stale_literal_patterns.items():
            if pattern.search(text):
                errors.append(f"{path}: forbidden current-value literal ({label})")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        print(f"Contract validation failed ({len(errors)} errors):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contract validation passed: 4 contracts, 4 fixtures, 21 skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
