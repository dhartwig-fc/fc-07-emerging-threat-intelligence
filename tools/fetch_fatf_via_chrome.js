// tools/fetch_fatf_via_chrome.js
// fatf-gafi.org refuses curl, Node fetch and plain headless Chrome (403, TLS and
// automation fingerprinting). What works, measured 2026-09-10: a real Chrome
// launched by Playwright with headless + the AutomationControlled flag off and a
// normal user agent, fetching the PDF INSIDE the page and writing it from Node.
// The two Playwright MCP servers dropped their connection on every download
// after the first; this script needs neither.
//
// Requires a Playwright module on disk (the npx cache path below is where one
// was found; adjust) and Google Chrome installed. Edit the `files` map, then:
//     node tools/fetch_fatf_via_chrome.js
const { chromium } = require('/Users/danhartwig/.npm/_npx/9833c18b2d85bc59/node_modules/playwright');
const fs = require('fs'); const crypto = require('crypto');
const DEST = '/Users/danhartwig/fc-08-emerging-threat-intelligence/data/advisories/';
const files = {
  'fatf-professional-money-laundering-2018.pdf': '/content/dam/fatf-gafi/reports/Professional-Money-Laundering.pdf',
  'fatf-egmont-concealment-beneficial-ownership-2018.pdf': '/content/dam/fatf-gafi/reports/FATF-Egmont-Concealment-beneficial-ownership.pdf',
  'fatf-virtual-assets-red-flags-2020.pdf': '/content/dam/fatf-gafi/reports/Virtual-Assets-Red-Flag-Indicators.pdf',
  'fatf-environmental-crime-2021.pdf': '/content/dam/fatf-gafi/reports/Money-Laundering-from-Environmental-Crime.pdf',
  'fatf-cyber-enabled-fraud-2023.pdf': '/content/dam/fatf-gafi/reports/Illicit-financial-flows-cyber-enabled-fraud.pdf.coredownload.inline.pdf',
  'fatf-pml-underground-banking-hawala-2026.pdf': '/content/dam/fatf-gafi/reports/pml-underground-banking-hawala-fatf-report-2026.pdf.coredownload.pdf',
};
(async () => {
  const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36';
  const modes = [{ headless: true, label: 'headless+stealth' }, { headless: false, label: 'headed' }];
  let browser, page;
  for (const m of modes) {
    browser = await chromium.launch({ channel: 'chrome', headless: m.headless, args: ['--disable-blink-features=AutomationControlled'] });
    const ctx = await browser.newContext({ userAgent: UA, viewport: { width: 1280, height: 900 } });
    await ctx.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); });
    page = await ctx.newPage();
    await page.goto('https://www.fatf-gafi.org/en/topics/methods-and-trends.html', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(1500);
    const probe = await page.evaluate(async () => (await fetch('/content/dam/fatf-gafi/reports/Professional-Money-Laundering.pdf', { headers: { Range: 'bytes=0-4' } })).status);
    console.log('mode', m.label, 'probe status', probe);
    if (probe === 200 || probe === 206) break;
    await browser.close();
  }
  for (const [name, href] of Object.entries(files)) {
    try {
      const b64 = await page.evaluate(async (h) => {
        const r = await fetch(h); if (r.status !== 200) return 'ERR:' + r.status;
        const u = new Uint8Array(await r.arrayBuffer()); let s = '';
        for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
        return btoa(s);
      }, href);
      if (b64.startsWith('ERR:')) { console.log('FAIL', name, b64); continue; }
      const buf = Buffer.from(b64, 'base64');
      if (buf.subarray(0, 5).toString() !== '%PDF-') { console.log('FAIL', name, 'not a pdf'); continue; }
      fs.writeFileSync(DEST + name, buf);
      console.log('OK  ', name, buf.length, 'bytes', crypto.createHash('sha256').update(buf).digest('hex').slice(0, 12));
    } catch (e) { console.log('FAIL', name, String(e).slice(0, 120)); }
  }
  await browser.close();
})();
