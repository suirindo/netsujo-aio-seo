# Visibility policy evaluations

`eval-cases.json` defines the 18 failure modes captured by the 2026-07-28
implementation brief. `scripts/run-evals.py` is a deterministic policy
regression: it verifies that every case has an explicit expected decision and
that its owning skill instructions still contain the required guardrails.

This runner does not sample an LLM and does not claim model-level accuracy. It
prevents publishing a plugin release after a required policy has silently
disappeared from the skill text. Contract shape and fixture behavior are tested
separately by `scripts/test-contracts.py`.

Run from the repository root:

```bash
python3 scripts/validate-contracts.py
python3 scripts/test-contracts.py
python3 scripts/run-evals.py
```
