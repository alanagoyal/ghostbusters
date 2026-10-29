const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');
const exportsObject = {};
runInNewContext(ts.transpileModule(readFileSync(require.resolve('../lib/detections.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { exports: exportsObject });
const { applyDetectionChange } = exportsObject;
const row = (id, timestamp = '2026-10-28T12:00:00Z') => ({ id, timestamp, image_url: 'original', thumbnail_url: 'thumb' });

test('live inserts are ordered, deduplicated and bounded to 200 records', () => {
  const initial = Array.from({length:200}, (_, i) => row(String(i).padStart(3, '0')));
  const next = applyDetectionChange(initial, { eventType: 'INSERT', old: {}, new: row('new', '2026-10-28T12:01:00Z') });
  assert.equal(next.length, 200);
  assert.equal(next[0].id, 'new');
  assert.equal(applyDetectionChange(next, {eventType:'INSERT', old:{}, new:next[0]}).length, 200);
});

test('partial classification updates retain photos and deletes need only the id', () => {
  const rows = [row('a'), row('b')];
  const updated = applyDetectionChange(rows, {eventType:'UPDATE', old:{}, new:{id:'a', costume_classification:'witch'}});
  assert.equal(updated.find(r => r.id === 'a').thumbnail_url, 'thumb');
  assert.equal(updated.find(r => r.id === 'a').costume_classification, 'witch');
  const deleted = applyDetectionChange(updated, {eventType:'DELETE', old:{id:'a'}, new:{}});
  assert.equal(deleted.length, 1);
  assert.equal(deleted[0].id, 'b');
});

test('events during reconciliation win over an older query snapshot', () => {
  const changes = [
    {eventType:'UPDATE', old:{}, new:{id:'a', costume_classification:'pirate'}},
    {eventType:'DELETE', old:{id:'b'}, new:{}},
    {eventType:'INSERT', old:{}, new:row('c', '2026-10-28T12:02:00Z')},
  ];
  const result = changes.reduce(applyDetectionChange, [row('a'), row('b')]);
  assert.equal(result.length, 2);
  assert.equal(result[0].id, 'c');
  assert.equal(result[1].costume_classification, 'pirate');
});
