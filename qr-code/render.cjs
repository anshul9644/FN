(async () => {
const { chromium } = require('playwright');
const path = require('node:path');
const dir = __dirname;
const out = process.argv[2];
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 3 });
await page.goto('file://' + path.join(dir, 'qr.html'), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.pdf({ path: path.join(dir, 'FreshNet-Website-QR.pdf'), preferCSSPageSize: true, printBackground: true });
if (out) {
  const pages = await page.$$('section.page');
  for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: path.join(out, `qr-p${i + 1}.png`) });
}
await browser.close();
})();
