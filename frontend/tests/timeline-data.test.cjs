const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');
const api = {};
runInNewContext(ts.transpileModule(readFileSync(require.resolve('../components/dashboard/timeline-data.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { exports: api });

test('years share evening slots without expanding the calendar gap', () => {
  const result = api.eveningTimeline([
    { timestamp: '2025-10-31T19:42:00' },
    { timestamp: '2026-10-31T19:42:00' },
    { timestamp: '2026-10-31T19:44:00' },
  ]);
  assert.ok(result.slots.length <= 96);
  assert.equal(result.series[0].year, 2026);
  const i = result.slots.findIndex(s => s.label === '7:30 PM');
  assert.equal(result.series[0].counts[i], 2);
  assert.equal(result.series[1].counts[i], 1);
});
test('midnight follows evening; empty and invalid data have no series', () => {
  const result = api.eveningTimeline([{ timestamp: '2025-10-31T23:55:00' }, { timestamp: '2025-11-01T00:10:00' }]);
  assert.ok(result.slots.findIndex(s => s.label === '12:00 AM') > result.slots.findIndex(s => s.label === '11:45 PM'));
  assert.equal(api.eveningTimeline([]).series.length, 0);
  assert.equal(api.eveningTimeline([{ timestamp: 'invalid' }]).slots.length, 0);
});
