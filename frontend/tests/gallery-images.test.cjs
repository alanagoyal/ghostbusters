const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');

function load(privateMode = true) {
  const calls = [];
  const exports = {};
  let now = 0;
  let denied = false;
  const source = ts.transpileModule(readFileSync(require.resolve('../lib/gallery-images.ts'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  runInNewContext(source, {
    exports, URL, Date: { now: () => now }, process: { env: {
      NEXT_PUBLIC_GALLERY_ACCESS: privateMode ? 'private' : undefined,
      NEXT_PUBLIC_SUPABASE_URL: 'https://test.supabase.co',
    } }, require: () => ({ supabase: { storage: { from(bucket) {
      return { async createSignedUrls(paths, ttl) {
        calls.push({ bucket, paths, ttl });
        if (denied) return { error: { message: 'denied' } };
        return { data: paths.map(path => path === 'missing.jpg' ? { path, error: 'denied' }
          : { path, signedUrl: 'https://test.supabase.co/signed/' + path + '?issued=' + now }) };
      } };
    } } } }),
  });
  return { ...exports, calls, time: value => { now = value; }, deny: () => { denied = true; } };
}

test('private records batch-sign scoped two-minute links and deduplicate objects', async () => {
  const api = load();
  const rows = await api.galleryImages([
    { image_url: 'device/photo.jpg' },
    { image_url: 'https://test.supabase.co/storage/v1/object/public/detection-images/old.jpg' },
    { image_url: 'device/photo.jpg' },
  ]);
  assert.equal(rows[0].image_url, 'https://test.supabase.co/signed/device/photo.jpg?issued=0');
  assert.equal(rows[1].image_url, 'https://test.supabase.co/signed/old.jpg?issued=0');
  assert.equal(api.calls.length, 1);
  assert.equal(api.calls[0].paths.length, 2);
  assert.equal(api.calls[0].ttl, 120);
  assert.equal(api.calls[0].bucket, 'detection-images');
  assert.ok(rows.every(row => row.image_unoptimized));
});

test('unknown origins, traversal and denied objects never fall back to public URLs', async () => {
  const api = load();
  const rows = await api.galleryImages([
    { image_url: 'https://elsewhere.example/photo.jpg' },
    { image_url: '/absolute.jpg' },
    { image_url: '../escape.jpg' },
    { image_url: 'https://test.supabase.co/storage/v1/object/public/detection-images/device%2F..%2Fescape.jpg' },
    { image_url: 'missing.jpg' },
  ]);
  assert.ok(rows.every(r => r.image_url === null));
  assert.equal(api.calls.length, 1);
  assert.equal(api.calls[0].paths.length, 1);
});

test('a mounted viewer reuses links, renews ahead of expiry, and forgets removed photos', async () => {
  const api = load();
  const cache = new Map();
  const rows = [{ image_url: 'device/photo.jpg' }];
  const first = await api.galleryImages(rows, cache);
  api.time(30_000);
  assert.equal((await api.galleryImages(rows, cache))[0].image_url, first[0].image_url);
  assert.equal(api.calls.length, 1);
  api.time(60_000);
  assert.notEqual((await api.galleryImages(rows, cache))[0].image_url, first[0].image_url);
  assert.equal(api.calls.length, 2);
  await api.galleryImages([], cache);
  assert.equal(cache.size, 0);
  await api.galleryImages(rows, new Map());
  assert.equal(api.calls.length, 3);
});

test('failed renewal removes old links instead of extending authorization', async () => {
  const api = load();
  const cache = new Map();
  const rows = [{ image_url: 'photo.jpg' }];
  await api.galleryImages(rows, cache);
  api.time(60_000);
  api.deny();
  assert.equal((await api.galleryImages(rows, cache))[0].image_url, null);
  assert.equal(cache.size, 0);
});

test('public legacy images retain the optimizer, while thumbnails bypass it', async () => {
  const api = load(false);
  const legacy = 'https://test.supabase.co/storage/v1/object/public/detection-images/old.jpg';
  const rows = await api.galleryImages([
    { image_url: legacy },
    { image_url: legacy, thumbnail_url: 'device/thumb.webp' },
  ]);
  assert.equal(rows[0].image_url, legacy);
  assert.equal(rows[0].image_unoptimized, false);
  assert.equal(rows[1].image_url, 'https://test.supabase.co/storage/v1/object/public/detection-images/device/thumb.webp');
  assert.equal(rows[1].image_unoptimized, true);
  assert.equal(api.calls.length, 0);
});

test('versioned paths work without a schema change and originals resolve only on demand', async () => {
  for (const privateMode of [true, false]) {
    const api = load(privateMode);
    const path = 'device/gallery-v1/' + 'a'.repeat(64) + '/original.jpg';
    const thumbnail = (await api.galleryImages([{ image_url: path }]))[0];
    assert.ok(thumbnail.image_url.includes('/thumbnail.webp'));
    assert.equal(thumbnail.image_unoptimized, true);
    const original = (await api.galleryImages([{ image_url: path }], new Map(), { original: true }))[0];
    assert.ok(original.image_url.includes('/original.jpg'));
    assert.equal(original.image_unoptimized, privateMode);
  }
});
