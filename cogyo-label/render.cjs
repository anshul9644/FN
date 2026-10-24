// Renders label.html → label.pdf (bleed + crop marks), label-preview.png (300 dpi),
// front-preview.png (front panel, 300 dpi) and mockup.png (3D tin).
// Usage: node render.cjs
const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');

const dir = __dirname;
const DPI = 300, SCALE = DPI / 96; // CSS px are 1/96 in
const url = f => 'file://' + path.join(dir, f);

(async () => {
  const browser = await chromium.launch();

  // ---- label at 300 dpi ----
  const page = await browser.newPage({ viewport: { width: 1200, height: 700 }, deviceScaleFactor: SCALE });
  await page.goto(url('label.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const d = await page.evaluate(() => window.__dims);

  const trim = await page.locator('#trim').boundingBox();
  const front = await page.locator('#p-front').boundingBox();
  const bleedPx = d.bleed * 96 / 25.4;
  // trim area (wrap + overlap) — what the shopper sees
  await page.screenshot({ path: path.join(dir, 'label-preview.png'), clip: trim });
  // front panel at trim height
  await page.screenshot({ path: path.join(dir, 'front-preview.png'), clip: { x: front.x, y: front.y + bleedPx, width: front.width, height: front.height - 2 * bleedPx } });
  // guides proof (not a deliverable for print, handy for checking)
  await page.evaluate(() => document.body.classList.add('show-guides'));
  await page.screenshot({ path: path.join(dir, 'label-guides.png'), clip: { x: trim.x - bleedPx, y: trim.y - bleedPx, width: trim.width + 2 * bleedPx, height: trim.height + 2 * bleedPx } });
  await page.evaluate(() => document.body.classList.remove('show-guides'));

  // ---- print PDF: whole sheet = bleed box + slug with crop marks ----
  // Chromium rasterises SVG/CSS filters at screen resolution when printing, so the
  // filtered art (hero illustration, seal shadow) is pre-rendered at 600 dpi as a
  // transparent PNG and swapped in. All text and flat shapes stay vector.
  const hi = await browser.newPage({ viewport: { width: 1200, height: 700 }, deviceScaleFactor: 600 / 96 });
  await hi.goto(url('label.html'), { waitUntil: 'networkidle' });
  await hi.evaluate(() => document.fonts.ready);
  await hi.evaluate(() => {
    document.documentElement.style.background = document.body.style.background = 'transparent';
    document.querySelector('.sheet').style.background = 'transparent';
    for (const e of document.querySelectorAll('.panel, .marks, .slugtxt')) e.style.visibility = 'hidden';
  });
  const art = {};
  for (const [sel, pad] of [['.hero', 0], ['.seal', 2.5]]) {
    await hi.evaluate(s => { const e = document.querySelector(s); e.style.visibility = 'visible'; e.querySelectorAll('*').forEach(c => c.style.visibility = 'visible'); }, sel);
    const bb = await hi.locator(sel).boundingBox(), p = pad * 96 / 25.4;
    const buf = await hi.screenshot({ omitBackground: true, clip: { x: bb.x - p, y: bb.y - p, width: bb.width + 2 * p, height: bb.height + 2 * p } });
    art[sel] = { src: 'data:image/png;base64,' + buf.toString('base64'), pad };
    await hi.evaluate(s => { document.querySelector(s).style.visibility = 'hidden'; }, sel);
  }
  await hi.close();
  await page.evaluate((art) => {
    for (const [sel, { src, pad }] of Object.entries(art)) {
      const e = document.querySelector(sel), img = document.createElement('img');
      const r = e.getBoundingClientRect(), pr = e.parentElement.getBoundingClientRect(); // SVG elements have no offsetLeft
      img.src = src;
      Object.assign(img.style, { position: 'absolute', display: 'block', left: `calc(${r.left - pr.left}px - ${pad}mm)`, top: `calc(${r.top - pr.top}px - ${pad}mm)`,
        width: `calc(${r.width}px + ${2 * pad}mm)`, height: `calc(${r.height}px + ${2 * pad}mm)` });
      e.replaceWith(img);
    }
  }, art);
  await page.waitForFunction(() => [...document.images].every(i => i.complete));
  const W = d.W + d.O + 2 * (d.bleed + d.slug), H = d.H + 2 * (d.bleed + d.slug);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: path.join(dir, 'label.pdf'), width: W + 'mm', height: H + 'mm', printBackground: true, pageRanges: '1' });

  // texture for the mockup: wrap only (no overlap), 2× less resolution is plenty
  const tex = await page.screenshot({ clip: { x: trim.x, y: trim.y, width: d.W * 96 / 25.4, height: trim.height } });
  await page.close();

  // ---- 3D tin mockup ----
  const m = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1 });
  await m.goto(url('mockup.html'));
  await m.evaluate(async (src) => window.drawMockup(src), 'data:image/png;base64,' + tex.toString('base64'));
  await m.locator('#stage').screenshot({ path: path.join(dir, 'mockup.png') });
  await browser.close();
  console.log('done', { sheet_mm: [W, H], dims: d });
})();
