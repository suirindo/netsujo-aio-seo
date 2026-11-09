import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, lstatSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const CLI = join(HERE, 'node_modules/@netsujo/agent-role-contracts/bin/agent-role-contracts.mjs');
export const REPORT = 'artifacts/arc-shadow/result.json';
export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

export function assess(result, expectedExit, expectedCode) {
  const stdout = result.stdout ?? '';
  const stderr = result.stderr ?? '';
  let parsed = null;
  try { parsed = JSON.parse(stdout); } catch { /* operational errors need not be JSON */ }
  const codes = parsed?.errors?.map((item) => item.code) ?? [];
  const actualCode = expectedExit === 2 && stderr.includes('ENOENT') ? 'ENOENT' : codes[0] ?? null;
  const checkerShape = parsed?.tool === 'agent-role-contracts' && parsed?.version === '1.0.0'
    && parsed?.execution_authorized === false && parsed?.runtime_enforcement === false;
  const expectedShape = expectedExit === 0
    ? checkerShape && parsed.valid === true && codes.length === 0
    : expectedExit === 1
      ? checkerShape && parsed.valid === false && codes.includes(expectedCode)
      : parsed?.valid !== true && actualCode === expectedCode;
  return {
    raw_exit: result.status, signal: result.signal, spawn_error: result.error?.message ?? null,
    expected_exit: expectedExit, expected_diagnostic: expectedCode, actual_diagnostic: actualCode,
    checker_valid: parsed?.valid ?? null,
    expectation_match: !result.error && !result.signal && result.status === expectedExit && Boolean(expectedShape),
    stdout, stderr,
  };
}

export function evaluate() {
  const bundle = readFileSync(join(HERE, 'bundle.json'));
  const original = readFileSync(join(HERE, 'task.json'));
  const task = JSON.parse(original);
  if (task.inputs.scope !== REPORT) throw new Error('Unexpected report scope; the output path is not configurable.');
  const outside = structuredClone(task);
  outside.inputs.scope = 'plugins/netsujo-aio/skills/pre-merge-test-suite/SKILL.md';
  const directory = mkdtempSync(join(tmpdir(), 'aio-arc-shadow-'));
  const cases = [];
  try {
    const bundlePath = join(directory, 'bundle.json');
    const taskPath = join(directory, 'task.json');
    writeFileSync(bundlePath, bundle);
    for (const [name, bytes, expectedExit, code] of [
      ['valid', original, 0, null],
      ['injected-outside-scope', Buffer.from(JSON.stringify(outside)), 1, 'TASK_WRITE_SCOPE_OUTSIDE_AUTHORITY'],
      ['restored-original', original, 0, null],
      ['malformed-json', Buffer.from('{broken\n'), 1, 'JSON_INVALID'],
      ['missing-input', null, 2, 'ENOENT'],
    ]) {
      if (bytes === null) rmSync(taskPath); else writeFileSync(taskPath, bytes);
      const args = [CLI, 'explain', '--bundle', bundlePath, '--task', taskPath, '--format', 'json'];
      const start = performance.now();
      const result = spawnSync(process.execPath, args, { encoding: 'utf8', timeout: 15_000, maxBuffer: 256 * 1024 });
      const unchanged = sha256(readFileSync(bundlePath)) === sha256(bundle)
        && (bytes === null ? !exists(taskPath) : sha256(readFileSync(taskPath)) === sha256(bytes));
      const observed = assess(result, expectedExit, code);
      cases.push({ name, classification: name === 'valid' ? 'NEW_INTERNAL_PILOT_DECLARATION' : 'INJECTED_CONTROL',
        command: [process.execPath, ...args], bundle_sha256: sha256(bundle),
        task_sha256: bytes === null ? null : sha256(bytes), inputs_unchanged: unchanged,
        wall_ms: Math.round((performance.now() - start) * 1000) / 1000,
        ...observed, expectation_match: observed.expectation_match && unchanged });
    }
  } finally { rmSync(directory, { recursive: true, force: true }); }
  const sourceUnchanged = sha256(readFileSync(join(HERE, 'bundle.json'))) === sha256(bundle)
    && sha256(readFileSync(join(HERE, 'task.json'))) === sha256(original);
  return { cases, source_inputs_unchanged: sourceUnchanged,
    restored_bytes_match: cases[0].task_sha256 === cases[2].task_sha256,
    expectation_match: sourceUnchanged && cases.every((row) => row.expectation_match) };
}

function exists(path) {
  try { lstatSync(path); return true; } catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

// Fixed local output only. This guard is runner code, NOT ARC runtime enforcement.
export function writeReport(root, report) {
  if (!report.cases?.[0]?.expectation_match || !report.cases?.[2]?.expectation_match || !report.restored_bytes_match) {
    throw new Error('Original report preflight was not accepted; report-file write withheld. See stdout.');
  }
  for (const relative of ['artifacts', 'artifacts/arc-shadow']) {
    const directory = join(root, relative);
    if (!exists(directory)) mkdirSync(directory);
    const stat = lstatSync(directory);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error('Report directory must not be a symlink.');
  }
  writeFileSync(join(root, REPORT), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}

function git(...args) {
  const result = spawnSync('git', ['-C', ROOT, ...args], { encoding: 'utf8', timeout: 5_000 });
  if (result.status !== 0) throw new Error('Consumer Git identity unavailable.');
  return result.stdout.trim();
}

export function main() {
  const installed = JSON.parse(readFileSync(join(HERE, 'node_modules/@netsujo/agent-role-contracts/package.json')));
  const lockBytes = readFileSync(join(HERE, 'package-lock.json'));
  const locked = JSON.parse(lockBytes).packages['node_modules/@netsujo/agent-role-contracts'];
  if (installed.name !== '@netsujo/agent-role-contracts' || installed.version !== '1.0.0' || locked.version !== '1.0.0') {
    throw new Error('Pinned ARC 1.0.0 installation required.');
  }
  const result = { classification: 'NEW_MAINTAINER_OPERATED_INTERNAL_CI_TRIAL',
    task: 'https://github.com/suirindo/netsujo-aio-seo/issues/18', observed_at: new Date().toISOString(),
    consumer_commit: git('rev-parse', 'HEAD'), source_diff_sha256: sha256(git('diff', 'HEAD', '--', '.github/workflows/test.yml', 'experiments/arc-shadow')),
    tracked_checkout_clean: git('status', '--porcelain', '--untracked-files=no') === '',
    source_files_sha256: Object.fromEntries(['.github/workflows/test.yml',
      ...['README.md', 'package.json', 'package-lock.json', 'bundle.json', 'task.json', 'check.mjs', 'check.test.mjs', '.gitignore']
        .map((name) => `experiments/arc-shadow/${name}`)]
      .map((name) => [name, sha256(readFileSync(join(ROOT, name)))])),
    node: process.version, platform: process.platform, arch: process.arch,
    package: installed.name, version: installed.version, integrity: locked.integrity,
    lock_sha256: sha256(lockBytes), run_url: process.env.GITHUB_RUN_ID
      ? `https://github.com/suirindo/netsujo-aio-seo/actions/runs/${process.env.GITHUB_RUN_ID}` : null,
    pr_head: process.env.ARC_PR_HEAD ?? null, execution_authorized: false, runtime_enforcement: false,
    organic_adoption: 'NOT_ESTABLISHED', external_adoption: 'NOT_ESTABLISHED', business_value: 'UNMEASURED',
    ...evaluate() };
  console.log(JSON.stringify(result, null, 2));
  writeReport(ROOT, result);
  console.log(`Raw ARC exits: ${result.cases.map((row) => row.raw_exit).join('/')}; harness expectations: ${result.expectation_match ? 'MATCH' : 'MISMATCH'}.`);
  return result.expectation_match ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.exitCode = main(); } catch (error) { console.error(`ARC_SHADOW_ERROR: ${error.message}`); process.exitCode = 2; }
}
