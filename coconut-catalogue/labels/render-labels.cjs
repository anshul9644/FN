(async () => {
const { chromium } = require('playwright');
const path = require('node:path');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 2000, height: 2000 } });
await page.goto('file://' + path.join(__dirname, 'labels.html'), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
for (const id of ['oil','testa','can','jar','box','flour','stamp','mct','butter','vco2','mct2','vco3','round','oilsticker']) {
  await (await page.$('#' + id)).screenshot({ path: path.join(__dirname, id + '.png'), omitBackground: true });
}
await browser.close();
})();
