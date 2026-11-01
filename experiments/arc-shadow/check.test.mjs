import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, symlinkSync, mkdirSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { assess, evaluate, writeReport, REPORT } from './check.mjs';

test('installed checker reproduces all five boundaries without mutating declarations', () => {
  const result = evaluate();
  assert.equal(result.expectation_match, true);
  assert.deepEqual(result.cases.map((row) => row.raw_exit), [0, 1, 0, 1, 2]);
  assert.equal(result.restored_bytes_match, true);
  assert.equal(result.source_inputs_unchanged, true);
});

test('zero exit or an unrelated diagnostic is not sufficient', () => {
  const fake = { status: 0, signal: null, stdout: '{}', stderr: '' };
  assert.equal(assess(fake, 0, null).expectation_match, false);
  assert.equal(assess({ ...fake, status: 1 }, 1, 'JSON_INVALID').expectation_match, false);
  assert.equal(assess({ ...fake, status: 2, stderr: 'OTHER_ERROR' }, 2, 'ENOENT').expectation_match, false);
  assert.equal(assess({ ...fake, signal: 'SIGTERM' }, 0, null).expectation_match, false);
  assert.equal(assess({ ...fake, error: new Error('spawn failed') }, 0, null).expectation_match, false);
  assert.equal(assess({ status: null, stdout: null, stderr: null, error: new Error('spawn failed') }, 2, 'ENOENT').expectation_match, false);
});

const permitted = { cases: [{ expectation_match: true }, {}, { expectation_match: true }], restored_bytes_match: true };
test('report writer requires accepted original and restored preflights', () => {
  const root = mkdtempSync(join(tmpdir(), 'aio-report-test-'));
  try {
    assert.throws(() => writeReport(root, { ...permitted, restored_bytes_match: false }), /withheld/);
    assert.equal(existsSync(join(root, 'artifacts')), false);
    writeReport(root, permitted);
    assert.deepEqual(JSON.parse(readFileSync(join(root, REPORT))), permitted);
    assert.throws(() => writeReport(root, permitted), { code: 'EEXIST' });
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('report writer rejects a symlinked output directory', () => {
  const root = mkdtempSync(join(tmpdir(), 'aio-report-test-'));
  try {
    const outside = join(root, 'outside');
    mkdirSync(outside);
    symlinkSync(outside, join(root, 'artifacts'));
    assert.throws(() => writeReport(root, permitted), /symlink/);
    assert.equal(existsSync(join(outside, 'arc-shadow/result.json')), false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
