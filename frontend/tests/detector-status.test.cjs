const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');
const exportsObject = {};
runInNewContext(ts.transpileModule(readFileSync(require.resolve('../lib/detector-status.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { exports: exportsObject });
const { detectorIsOnline } = exportsObject;
const now = Date.parse('2026-10-31T22:00:00Z');
const status = (age, running = true) => ({ running, updated_at: new Date(now - age).toISOString() });

test('recent processed frames mean live without requiring a person detection', () => {
  assert.equal(detectorIsOnline(status(0), now), true);
  assert.equal(detectorIsOnline(status(89_999), now), true);
});
test('stopping, crashing or losing the camera expires liveness', () => {
  assert.equal(detectorIsOnline(status(0, false), now), false);
  assert.equal(detectorIsOnline(status(90_000), now), false);
  assert.equal(detectorIsOnline(status(120_000), now), false);
});
test('missing, malformed and future status never gives a live light', () => {
  for (const value of [null, {}, {running: true}, {running: 'true', updated_at: status(0).updated_at}, {running: true, updated_at: 'bad'}, status(-60_000)]) {
    assert.equal(detectorIsOnline(value, now), false);
  }
});
