const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');

function load(file, modules, globals = {}) {
  const exports = {};
  const code = ts.transpileModule(readFileSync(require.resolve(file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  runInNewContext(code, { exports, require: name => {
    assert.ok(name in modules, `Unexpected import: ${name}`);
    return modules[name];
  }, ...globals });
  return exports;
}

test('public gallery fetches new captures on mount without waiting for Realtime', async () => {
  let effect, fetches = 0;
  const states = [];
  const latest = [{ id: 'new-capture', timestamp: '2026-10-31T17:29:00-07:00', image_url: 'photo' }];
  const query = { select: () => query, order: () => query, limit: async () => {
    fetches++;
    return { data: latest, error: null };
  }};
  // Subscription never reaches SUBSCRIBED, as with blocked/slow WebSockets.
  const channel = { on: () => channel, subscribe: () => channel };
  const { useDetections } = load('../lib/use-detections.ts', {
    react: { useRef: current => ({ current }), useCallback: f => f,
      useEffect: f => { effect = f; }, useState: value => {
        const slot = { value: typeof value === 'function' ? value() : value };
        states.push(slot);
        return [slot.value, value => { slot.value = value; }];
      } },
    '@/lib/use-detector-status': { useDetectorStatus: () => false },
    '@/lib/supabase': { supabase: { from: () => query, channel: () => channel, removeChannel: () => {} } },
    '@/lib/detections': { applyDetectionChange: () => { throw Error('No live events expected'); } },
    '@/lib/gallery-images': { privateGallery: false, publicGalleryImages: rows => rows, galleryImages: async rows => rows },
  }, { setInterval: () => 1, clearInterval: () => {}, setTimeout, clearTimeout,
    document: { addEventListener() {}, removeEventListener() {} },
    window: { addEventListener() {}, removeEventListener() {} } });
  useDetections([{ id: 'old-capture', timestamp: '2025-10-31T17:00:00-07:00' }]);
  const cleanup = effect();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(fetches, 1);
  assert.equal(states[0].value[0].id, 'new-capture');
  assert.equal(states[1].value[0].id, 'new-capture');
  cleanup();
});

test('cloud render reads after request-time connection; local export needs neither', async () => {
  const env = { NEXT_PUBLIC_SUPABASE_URL: 'https://example.supabase.co' };
  const calls = [];
  const query = { select: () => query, order: () => query, limit: async () => {
    calls.push('query'); return { data: [], error: null };
  }};
  const page = load('../app/page.tsx', {
    'react/jsx-runtime': { jsx: (type, props) => ({ type, props }) },
    'next/server': { connection: async () => { calls.push('connection'); } },
    '@/components/private-gallery': { PrivateGallery: 'private' },
    '@/components/local-gallery': { LocalGallery: 'local' },
    '@/components/dashboard/dashboard-client': { DashboardClient: 'cloud' },
    '@/lib/supabase': { supabase: { from: () => query } },
  }, { process: { env }, console });
  assert.equal((await page.default()).type, 'cloud');
  assert.deepEqual(calls, ['connection', 'query']);
  calls.length = 0;
  env.NEXT_PUBLIC_STORAGE_PROVIDER = 'local';
  assert.equal((await page.default()).type, 'local');
  assert.deepEqual(calls, []);
});
