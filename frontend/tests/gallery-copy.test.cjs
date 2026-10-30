const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const ts = require('typescript');
const source = ts.transpileModule(readFileSync(require.resolve('../lib/gallery-copy.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText;

function copy(env) {
  const exports = {};
  runInNewContext(source, { exports, process: { env } });
  return exports.galleryCopy;
}

test('fresh clones get generic copy without a scheduled return', () => {
  const defaults = copy({});
  assert.equal(defaults.offlineMessage, '');
  assert.equal(defaults.steps.length, 5);
  assert.equal(defaults.subtitle, 'A live feed of trick-or-treaters’ costumes.');
  assert.equal(copy({ NEXT_PUBLIC_GALLERY_SUBTITLE: '' }).subtitle, defaults.subtitle);
});

test('deployment copy overrides individual fields without replacing other defaults', () => {
  const defaults = copy({});
  const custom = copy({
    NEXT_PUBLIC_GALLERY_SUBTITLE: 'My costume camera',
    NEXT_PUBLIC_GALLERY_OFFLINE_MESSAGE: 'Back tomorrow at 3pm',
    NEXT_PUBLIC_GALLERY_CLASSIFY_TEXT: 'Our configured model describes costumes.',
  });
  assert.equal(custom.subtitle, 'My costume camera');
  assert.equal(custom.offlineMessage, 'Back tomorrow at 3pm');
  assert.equal(custom.steps[3][1], 'Our configured model describes costumes.');
  assert.equal(custom.steps[0][1], defaults.steps[0][1]);
  assert.equal(copy({}).offlineMessage, '');
});
