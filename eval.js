const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROMIUM_PATH = '/data/data/com.termux/files/usr/bin/chromium-browser';
const PROJECT_DIR = path.resolve(__dirname);
const HTML_PATH = 'file://' + PROJECT_DIR + '/index.html';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function generateTestPDF(pageCount) {
  let lines = ['%PDF-1.4'];
  lines.push('1 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj');
  let kids = [];
  let parentNum = 2;
  for (let i = 0; i < pageCount; i++) {
    let stream = 'BT /F1 20 Tf 50 750 Td (Page_' + (i + 1) + ') Tj ET\n';
    for (let j = 0; j < 20; j++) {
      stream += 'BT /F1 9 Tf 50 ' + (710 - j * 30) + ' Td (Lorem_ipsum_dolor_sit_amet_consectetur_adipiscing_elit_sed_do_eiusmod_tempor_incididunt_ut_labore_et_dolore_magna_aliqua_.) Tj ET\n';
    }
    let s = lines.length + 1;
    lines.push(s + ' 0 obj<</Length ' + stream.length + '>>stream\n' + stream + '\nendstream\nendobj');
    let p = lines.length + 1;
    kids.push(p);
    lines.push(p + ' 0 obj<</Type/Page/Parent ' + parentNum + ' 0 R/MediaBox[0 0 612 792]/Contents ' + s + ' 0 R/Resources<</Font<</F1 1 0 R>>>>>>endobj');
  }
  lines.splice(1, 0, parentNum + ' 0 obj<</Type/Pages/Kids[' + kids.join(' ') + ']/Count ' + pageCount + '>>endobj');
  let root = lines.length + 1;
  lines.push(root + ' 0 obj<</Type/Catalog/Pages ' + parentNum + ' 0 R>>endobj');
  let body = lines.join('\n') + '\n';
  let xref = 'xref\n0 ' + (root + 1) + '\n0000000000 65535 f \n';
  let pos = 0;
  for (let l of lines) {
    xref += String(pos).padStart(10, '0') + ' 00000 n \n';
    pos += l.length + 1;
  }
  body += xref + 'trailer<</Size ' + (root + 1) + '/Root ' + root + ' 0 R>>\nstartxref\n' + pos + '\n%%EOF';
  return Buffer.from(body);
}

async function main() {
  const split = process.argv.includes('--split') ? process.argv[process.argv.indexOf('--split') + 1] || 'dev' : 'dev';
  
  try {
    const testPdf = path.join(PROJECT_DIR, '_test_bench.pdf');
    fs.writeFileSync(testPdf, generateTestPDF(20));
    
    const browser = await puppeteer.launch({
      executablePath: CHROMIUM_PATH,
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });
    
    const page = await browser.newPage();
    await page.goto(HTML_PATH, { waitUntil: 'networkidle0', timeout: 30000 });
    await sleep(2000);
    
    // Upload PDF
    const fi = await page.$('#fileInput');
    if (fi) {
      await fi.uploadFile(testPdf);
      await sleep(4000);
    }
    
    const results = await page.evaluate(async () => {
      const E = window.__exports;
      if (!E) return { composite: 0, scroll_fps: 0, hud_latency: 0, page_turn: 0 };
      
      // Switch to waterfall mode
      E.togglePageMode();
      await new Promise(r => setTimeout(r, 2000));
      
      // Render page 1 in waterfall
      await E.renderPage(1);
      await new Promise(r => setTimeout(r, 3000));
      
      // --- 1. Scroll FPS ---
      const frameTimes = [];
      let lastTime = performance.now();
      let running = true;
      function frame(time) {
        if (!running) return;
        const d = time - lastTime;
        if (d > 0 && d < 100) frameTimes.push(d);
        lastTime = time;
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
      
      const reader = document.getElementById('reader');
      let pos = 0;
      const si = setInterval(() => {
        pos += 80;
        if (reader) reader.scrollTo({ top: pos, behavior: 'instant' });
        if (pos > 10000) pos = 0;
      }, 16);
      
      await new Promise(r => setTimeout(r, 3000));
      running = false;
      clearInterval(si);
      
      const scroll_fps = frameTimes.length > 0
        ? 1000 / (frameTimes.reduce((a,b)=>a+b,0) / frameTimes.length)
        : 30;
      
      // --- 2. HUD latency ---
      let hud_latency = 300;
      try {
        const t0 = performance.now();
        E.toggleHUD();
        hud_latency = performance.now() - t0;
        E.toggleHUD();
      } catch(e) {}
      
      // --- 3. Page turn (async) ---
      let page_turn = 150;
      try {
        const t0 = performance.now();
        await E.renderPage(5);
        page_turn = performance.now() - t0;
      } catch(e) {}
      
      const composite = Math.max(0, scroll_fps * 10 - hud_latency * 0.1 - page_turn * 0.1);
      return { composite, scroll_fps, hud_latency, page_turn };
    });
    
    await browser.close();
    try { fs.unlinkSync(testPdf); } catch(e) {}
    
    console.log('score: ' + (results.composite || 0).toFixed(2));
    console.log('scroll_fps: ' + (results.scroll_fps || 0).toFixed(1));
    console.log('hud_latency: ' + (results.hud_latency || 0).toFixed(1));
    console.log('page_turn: ' + (results.page_turn || 0).toFixed(1));
    process.exit(0);
  } catch(err) {
    console.error('Error: ' + err.message);
    console.log('score: 0');
    process.exit(1);
  }
}

main();
