const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');

function load(privateMode = true) {
  const calls = [];
  const exports = {};
  const source = ts.transpileModule(readFileSync(require.resolve('../lib/gallery-images.ts'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  runInNewContext(source, {
    exports, URL, process: { env: {
      NEXT_PUBLIC_GALLERY_ACCESS: privateMode ? 'private' : undefined,
      NEXT_PUBLIC_SUPABASE_URL: 'https://test.supabase.co',
    } }, require: () => ({ supabase: { storage: { from(bucket) {
      return { async createSignedUrl(path, ttl) {
        calls.push({ bucket, path, ttl });
        return path === 'missing.jpg' ? { error: { message: 'denied' } }
          : { data: { signedUrl: 'https://test.supabase.co/signed/' + path } };
      } };
    } } } }),
  });
  return { ...exports, calls };
}

test('private records use scoped two-minute links, including legacy same-project URLs', async () => {
  const api = load();
  const rows = await api.galleryImages([
    { image_url: 'device/photo.jpg' },
    { image_url: 'https://test.supabase.co/storage/v1/object/public/detection-images/old.jpg' },
  ]);
  assert.equal(rows[0].image_url, 'https://test.supabase.co/signed/device/photo.jpg');
  assert.equal(rows[1].image_url, 'https://test.supabase.co/signed/old.jpg');
  assert.equal(api.calls.length, 2);
  assert.ok(api.calls.every(c => c.bucket === 'detection-images' && c.ttl === 120));
});

test('unknown origins and denied objects never fall back to public URLs', async () => {
  const api = load();
  const rows = await api.galleryImages([
    { image_url: 'https://elsewhere.example/photo.jpg' },
    { image_url: '/absolute.jpg' },
    { image_url: '../escape.jpg' },
    { image_url: 'missing.jpg' },
  ]);
  assert.ok(rows.every(r => r.image_url === null));
  assert.equal(api.calls.length, 1);
});

test('existing legacy galleries retain their URL behavior', async () => {
  const api = load(false);
  const rows = [{ image_url: 'https://legacy.example/photo.jpg' }];
  assert.equal(await api.galleryImages(rows), rows);
  assert.equal(api.calls.length, 0);
});
