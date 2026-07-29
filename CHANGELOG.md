# Changelog

## 0.5.0 — 2026-07-29

- Added `goal-backcast-visibility-map`, which connects approved business goals,
  decisions, conversions, search keywords, AI questions, evidence, destination
  pages, CTAs, and measurement.
- Added strict v1 contracts for the target registry, AI citation snapshots,
  community-stat snapshots, and dashboard imports.
- Added dependency-free validators, negative contract tests, and deterministic
  E01–E18 policy regressions to CI.
- Defined stable AI citation as at least three successful repeats under the same
  engine/model/locale/variant condition.
- Defined the canonical mutable-stat lineage: complete pagination, a versioned
  inclusion rule, immutable success snapshot, last-known-good fallback, atomic
  publishing, and build-pinned consumers.
- Removed stale current-value literals and unsupported citation-lift claims from
  shipped skill guidance.
