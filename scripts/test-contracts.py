#!/usr/bin/env python3
"""Regression tests for the public visibility-map contracts."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-contracts.py"
SNAPSHOT_ADAPTER_PATH = (
    ROOT
    / "plugins"
    / "netsujo-aio"
    / "skills"
    / "ai-citation-tracker"
    / "scripts"
    / "snapshot.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_contracts", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load contract validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_snapshot_adapter():
    spec = importlib.util.spec_from_file_location(
        "ai_citation_snapshot", SNAPSHOT_ADAPTER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load AI citation snapshot adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()

    def load_fixture(self, name: str):
        path = (
            ROOT
            / "plugins"
            / "netsujo-aio"
            / "skills"
            / "goal-backcast-visibility-map"
            / "evals"
            / "fixtures"
            / name
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_repository_contracts_are_consistent(self):
        self.assertEqual([], self.validator.validate_repository(ROOT))

    def test_ai_snapshot_rejects_answer_body_and_single_run_stable(self):
        fixture = self.load_fixture("ai-citation-snapshot.valid.json")

        with_answer = copy.deepcopy(fixture)
        with_answer["observations"][0]["answerBody"] = "must not be stored"
        self.assertTrue(
            any(
                "forbidden" in error
                for error in self.validator.validate_ai_snapshot(with_answer)
            )
        )

        single_run_stable = copy.deepcopy(fixture)
        single_run_stable["observations"][0]["runCount"] = 1
        single_run_stable["observations"][0]["successCount"] = 1
        single_run_stable["observations"][0]["ownCitationCount"] = 1
        single_run_stable["observations"][0]["stability"] = "stable"
        self.assertTrue(
            any(
                "stable" in error
                for error in self.validator.validate_ai_snapshot(single_run_stable)
            )
        )

    def test_ai_snapshot_rejects_secrets_bad_counts_and_snapshot_mismatch(self):
        fixture = self.load_fixture("ai-citation-snapshot.valid.json")

        secret = copy.deepcopy(fixture)
        secret["observations"][0]["metadata"] = {
            "authorizationToken": "do-not-store"
        }
        self.assertTrue(self.validator.validate_ai_snapshot(secret))

        bad_counts = copy.deepcopy(fixture)
        bad_counts["observations"][0]["ownCitationCount"] = 4
        self.assertTrue(self.validator.validate_ai_snapshot(bad_counts))

        mismatch = copy.deepcopy(fixture)
        mismatch["observations"][0]["snapshotRef"] = "another-snapshot"
        self.assertTrue(self.validator.validate_ai_snapshot(mismatch))

    def test_stats_snapshot_requires_balanced_breakdown(self):
        fixture = self.load_fixture("community-stats-snapshot.valid.json")
        fixture["eventBreakdown"]["completed"] -= 1
        self.assertTrue(self.validator.validate_community_stats_snapshot(fixture))

    def test_visibility_registry_rejects_duplicate_and_orphan_targets(self):
        fixture = self.load_fixture("visibility-targets.valid.json")
        duplicate = copy.deepcopy(fixture)
        duplicate["targets"].append(copy.deepcopy(duplicate["targets"][0]))
        self.assertTrue(self.validator.validate_visibility_registry(duplicate))

        orphan = copy.deepcopy(fixture)
        orphan["targets"][0]["goalId"] = "UNKNOWN"
        self.assertTrue(self.validator.validate_visibility_registry(orphan))

    def test_contracts_reject_unsupported_versions(self):
        fixtures_and_validators = [
            (
                "visibility-targets.valid.json",
                self.validator.validate_visibility_registry,
            ),
            (
                "ai-citation-snapshot.valid.json",
                self.validator.validate_ai_snapshot,
            ),
            (
                "community-stats-snapshot.valid.json",
                self.validator.validate_community_stats_snapshot,
            ),
            (
                "visibility-dashboard-import.valid.json",
                self.validator.validate_dashboard_import,
            ),
        ]
        for fixture_name, validator in fixtures_and_validators:
            with self.subTest(fixture=fixture_name):
                fixture = self.load_fixture(fixture_name)
                fixture["schemaVersion"] = 2
                self.assertTrue(validator(fixture))

    def test_stats_snapshot_rejects_refresh_fields_and_dashboard_keeps_axes(self):
        stats = self.load_fixture("community-stats-snapshot.valid.json")
        stats["status"] = "stale"
        self.assertTrue(self.validator.validate_community_stats_snapshot(stats))

        dashboard = self.load_fixture("visibility-dashboard-import.valid.json")
        del dashboard["rows"][0]["aiStatus"]
        self.assertTrue(self.validator.validate_dashboard_import(dashboard))

    def test_dashboard_rejects_seed_only_measured_and_duplicate_rows(self):
        dashboard = self.load_fixture("visibility-dashboard-import.valid.json")
        dashboard["searchIntegration"] = "measured"
        dashboard["searchSnapshotId"] = None
        self.assertTrue(self.validator.validate_dashboard_import(dashboard))

        dashboard = self.load_fixture("visibility-dashboard-import.valid.json")
        dashboard["rows"].append(copy.deepcopy(dashboard["rows"][0]))
        self.assertTrue(self.validator.validate_dashboard_import(dashboard))

    def test_snapshot_adapter_emits_strict_contract_without_query(self):
        adapter = load_snapshot_adapter()
        snapshot = adapter.build_snapshot(
            site_id="netsujo",
            target_id="N-A-11",
            variant_id="N-A-11-v1",
            engine="perplexity",
            model="sonar",
            locale="ja-JP",
            brand_hosts=["netsujo.jp"],
            citations=[
                "https://netsujo.jp/services/signal",
                "https://competitor.example/guide",
            ],
            observed_at="2026-07-29T10:00:00.000Z",
        )
        self.assertEqual([], self.validator.validate_ai_snapshot(snapshot))
        serialized = json.dumps(snapshot, ensure_ascii=False).lower()
        self.assertNotIn("京都 web3 開発会社", serialized)
        self.assertEqual(
            "volatile", snapshot["observations"][0]["stability"]
        )


if __name__ == "__main__":
    unittest.main()
