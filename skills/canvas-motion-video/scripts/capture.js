// 逐帧渲染并导出 PNG：node capture.js [--out frames] [--frames 0,45,100] [--log qa/textlog.json]
// 与 index.html 同目录，或放在其下的 scripts/。相对的 --out / --log 相对 index.html 所在目录，不看当前工作目录。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };

function projectRoot() {
  if (fs.existsSync(path.join(__dirname, 'index.html'))) return __dirname;
  const parent = path.resolve(__dirname, '..');
  if (fs.existsSync(path.join(parent, 'index.html'))) return parent;
  throw new Error('找不到 index.html。请把脚本放在 index.html 同目录，或放在其下的 scripts/ 目录。');
}
const root = projectRoot();
const fromRoot = (p) => (path.isAbsolute(p) ? p : path.resolve(root, p));
const outDir = fromRoot(opt('--out', 'frames'));
const list = opt('--frames', null);
const logArg = opt('--log', null);
const logPath = logArg ? fromRoot(logArg) : null;
const frames = list ? list.split(',').map(Number) : Array.from({ length: 1200 }, (_, i) => i);

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, 'index.html'));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(window.FONT_SPECS.map(s => document.fonts.load(s, '测试中文 ABC 0123 ×')));
    await document.fonts.ready;
  });
  return page;
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await openPage(browser);
  const logs = {};
  for (const f of frames) {
    const { url, texts } = await page.evaluate((fr) => {
      const texts = window.render(fr);
      return { url: document.getElementById('c').toDataURL('image/png'), texts };
    }, f);
    fs.writeFileSync(path.join(outDir, String(f).padStart(4, '0') + '.png'), Buffer.from(url.split(',')[1], 'base64'));
    if (logPath) logs[f] = texts;
    if (f % 100 === 0) process.stdout.write(`frame ${f}\n`);
  }
  if (logPath) {
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.writeFileSync(logPath, JSON.stringify(logs, null, 1));
  }
  await browser.close();
})();
