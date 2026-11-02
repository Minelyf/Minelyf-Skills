// 验收：文字越界/重叠 + 中帧两次独立渲染像素一致
// 与 index.html 同目录，或放在其下的 scripts/。报告写到 index.html 同级的 qa/，不看当前工作目录。
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const CHECK = [100, 240, 380, 470, 570, 660, 780, 930, 1050, 1160];
const SAFE = 110, W = 1920, H = 1080;
const PIX_FRAME = 600;

function projectRoot() {
  if (fs.existsSync(path.join(__dirname, 'index.html'))) return __dirname;
  const parent = path.resolve(__dirname, '..');
  if (fs.existsSync(path.join(parent, 'index.html'))) return parent;
  throw new Error('找不到 index.html。请把脚本放在 index.html 同目录，或放在其下的 scripts/ 目录。');
}
const root = projectRoot();
const qaDir = path.join(root, 'qa');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto('file://' + path.join(root, 'index.html'));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(window.FONT_SPECS.map(s => document.fonts.load(s, '测试中文 ABC 0123 ×')));
  });
  return page;
}
const grab = (page, f) => page.evaluate((fr) => { const t = window.render(fr); return { url: document.getElementById('c').toDataURL('image/png'), t }; }, f);

(async () => {
  fs.mkdirSync(qaDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await openPage(browser);
  const report = [];
  let globalIssues = [];
  for (let f = 0; f < 1200; f++) {
    const texts = await page.evaluate((fr) => window.render(fr), f);
    const issues = [];
    for (const t of texts) {
      if (t.x0 < SAFE - 0.5 || t.x1 > W - SAFE + 0.5 || t.y0 < SAFE - 0.5 || t.y1 > H - SAFE + 0.5)
        issues.push(`越界: "${t.s}" [${t.x0.toFixed(0)},${t.y0.toFixed(0)}–${t.x1.toFixed(0)},${t.y1.toFixed(0)}]`);
    }
    for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j];
      if (a.g && a.g === b.g) continue; // same kinetic line: segments laid out side by side
      if (a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1) issues.push(`重叠: "${a.s}" × "${b.s}"`);
    }
    if (issues.length) globalIssues.push({ f, issues });
    if (CHECK.includes(f)) {
      const { url } = await grab(page, f);
      fs.writeFileSync(path.join(qaDir, `frame_${String(f).padStart(4, '0')}.png`), Buffer.from(url.split(',')[1], 'base64'));
      report.push({ frame: f, texts: texts.map(t => t.s), issues });
    }
  }
  const p1 = await openPage(browser);
  const a = (await grab(p1, PIX_FRAME)).url;
  const p2 = await openPage(browser);
  await grab(p2, 1199); await grab(p2, 37); await grab(p2, 870);
  const b = (await grab(p2, PIX_FRAME)).url;
  const ba = Buffer.from(a.split(',')[1], 'base64'), bb = Buffer.from(b.split(',')[1], 'base64');
  fs.writeFileSync(path.join(qaDir, `f${PIX_FRAME}_a.png`), ba); fs.writeFileSync(path.join(qaDir, `f${PIX_FRAME}_b.png`), bb);
  const pix = await p1.evaluate(async ([ua, ub]) => {
    const load = (u) => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.src = u; });
    const [ia, ib] = await Promise.all([load(ua), load(ub)]);
    const cv = (im) => { const c = new OffscreenCanvas(im.width, im.height); const x = c.getContext('2d'); x.drawImage(im, 0, 0); return x.getImageData(0, 0, im.width, im.height).data; };
    const da = cv(ia), db = cv(ib); let diff = 0;
    for (let i = 0; i < da.length; i++) if (da[i] !== db[i]) diff++;
    return { len: da.length, diff };
  }, [a, b]);
  const md5 = (x) => crypto.createHash('md5').update(x).digest('hex');
  const out = { checkFrames: report, framesWithIssues: globalIssues,
    framePix: { frame: PIX_FRAME, md5_a: md5(ba), md5_b: md5(bb), pixelBytes: pix.len, differingBytes: pix.diff, identical: pix.diff === 0 } };
  fs.writeFileSync(path.join(qaDir, 'qa_report.json'), JSON.stringify(out, null, 1));
  console.log(JSON.stringify({ check: report.map(r => ({ f: r.frame, n: r.texts.length, issues: r.issues })), framesWithIssues: globalIssues.length, firstIssues: globalIssues.slice(0, 20), framePix: out.framePix }, null, 1));
  await browser.close();
})();
