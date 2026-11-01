# Optional ARC shadow trial

This is a **new maintainer-operated internal CI trial**, tracked in
[issue #18](https://github.com/suirindo/netsujo-aio-seo/issues/18). It is not
prior organic adoption, external evaluation, an SEO finding or a runtime guard.
The existing skills and Python validation job are unchanged.

## What is actually checked

The newly declared `ci-evidence-writer` prepares this trial's own report at
`artifacts/arc-shadow/result.json`. The runner checks that narrow declaration
before writing the report to its fixed path. It never writes to the skill path
used in the negative control. Checkout, dependency installation, CI configuration
and the rest of the PR are **not** modeled by this report-writing declaration.

ARC checks supplied declarations, not actual OS access, identity or evidence
authenticity. The runner's fixed-path and no-overwrite checks are its own code,
not ARC enforcement. Policy and task are in the same PR: this is not an
independently trusted policy boundary. The declared read-only reviewer is an
intended route, not proof that independent review happened. No reviewer identity,
human approval or SEO execution is inferred. A PASS grants no execution, merge
or publication authority.

## Reproduce

From the repository root, using Node.js 22.5+ (hosted job: 24.22.1):

```sh
npm --prefix experiments/arc-shadow ci --ignore-scripts --include=dev --no-audit --no-fund
npm --prefix experiments/arc-shadow test
npm --prefix experiments/arc-shadow run check
```

The private consumer locks `@netsujo/agent-role-contracts` to **1.0.0** and its
npm integrity. It imports the installed package, not ARC's repository source.
The report is created once; an existing report is not overwritten. Use a fresh
checkout for another evidence-producing run. Tests use temporary directories.

| Case | Expected raw ARC exit | Interpretation |
| --- | ---: | --- |
| Valid report declaration | 0 | New pilot's report-writing preflight |
| Injected skill-path scope | 1 | `TASK_WRITE_SCOPE_OUTSIDE_AUTHORITY` expected |
| Restored original bytes | 0 | Reaccept the original declaration |
| Malformed JSON | 1 | `JSON_INVALID` expected |
| Missing task input | 2 | `ENOENT`; must not report PASS |

The last four rows are **injected controls**. Restoration is not a naturally
discovered business defect. Raw checker rejection and the test harness matching
that expected rejection are separate fields in the JSON. Unexpected diagnostics,
timeouts, installation errors and missing outputs are not successful validation.

## Hosted evidence and limits

The existing `Smoke test` workflow adds one short, non-blocking Linux job with a
read-only token and no stored checkout credential. Its logs preserve raw output;
the artifact records the checkout commit, PR head, run URL, Node version, source
hashes, exact commands and input hashes. Optional-job failure does not replace or
weaken the existing Python checks; inspect the shadow job and artifact explicitly.

The workflow uses only GitHub Actions and npm; no model, SEO API, credential,
deployment or paid API is invoked. Until a run exists, hosted acceptance is
`NOT_RUN`. A successful run demonstrates this explicit CI trial only: organic
reuse, human time saved, incremental business value and external adoption remain
unmeasured or unestablished.
