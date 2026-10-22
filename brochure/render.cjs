(async () => {
const { chromium } = require('playwright');
const path = require('node:path');
const dir = __dirname;
const out = process.argv[2] || dir;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
await page.goto('file://' + path.join(dir, 'brochure.html'), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.pdf({ path: path.join(dir, 'FreshNet-Farms-Catalogue.pdf'), preferCSSPageSize: true, printBackground: true });
if (process.argv[2]) {
  const pages = await page.$$('section.page');
  for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: path.join(out, `p${String(i + 1).padStart(2, '0')}.png`) });
}
await browser.close();
})();
