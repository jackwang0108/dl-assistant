'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { serve } = require('./lib');
async function open(html, exportMode = false, printMode = false) {
  const root = path.dirname(path.resolve(html));
  const { server, origin } = await serve(root);
  let browser;
  try {
    const puppeteer = require('puppeteer');
    const candidates = [process.env.PUPPETEER_EXECUTABLE_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'].filter(Boolean);
    const executablePath = candidates.find(f => fs.existsSync(f));
    browser = await puppeteer.launch({ headless: true, executablePath, timeout: 15000 });
    const page = await browser.newPage();
    const issues = [];
    await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
    await page.setRequestInterception(true);
    page.on('request', r => {
      if (!r.url().startsWith(origin + '/') && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) {
        issues.push({ kind: 'external_resource', url: r.url().split('?')[0] }); r.abort();
      } else r.continue();
    });
    page.on('pageerror', error => issues.push({ kind: 'javascript', message: error.message }));
    page.on('response', response => { if (response.status() >= 400) issues.push({ kind: 'http', status: response.status(), url: response.url().split('?')[0] }); });
    page.on('requestfailed', r => { if (r.url().startsWith(origin + '/')) issues.push({ kind: 'resource_failed', url: r.url() }); });
    const url = `${origin}/${encodeURIComponent(path.basename(html))}${exportMode ? '?export' : ''}${printMode ? '&print-pdf' : ''}`;
    await page.goto(url, { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.Reveal?.isReady() && window.presentationSettled === true, { timeout: 30000 });
    issues.push(...await page.evaluate(() => (window.presentationErrors || []).map(message => ({ kind: 'render', message }))));
    await page.evaluate(() => Reveal.configure({ transition: 'none', autoAnimate: false }));
    const slides = await page.evaluate(() => Reveal.getSlides().map((s, i) => ({ index: i + 1, id: s.id, ...Reveal.getIndices(s), fragments: Array.from(s.querySelectorAll('.fragment')).map(x => Number(x.dataset.fragmentIndex)).filter(Number.isFinite) })));
    return { page, issues, slides, browser, server, close: async () => { await browser.close(); await new Promise(resolve => server.close(resolve)); } };
  } catch (error) {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    throw error;
  }
}
async function visit(page, slide, fragment = -1) {
  await page.evaluate(({ h, v, fragment }) => { Reveal.slide(h, v || 0, fragment); Reveal.layout(); if (window.Chart) for (const chart of Object.values(Chart.instances)) { chart.resize(); chart.update('none'); } }, { h: slide.h, v: slide.v, fragment });
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await new Promise(resolve => setTimeout(resolve, 100));
}
async function overflow(page) {
  return page.evaluate(() => {
    const slide = Reveal.getCurrentSlide(), bounds = slide.getBoundingClientRect();
    const offenders = [];
    for (const el of slide.querySelectorAll('*')) {
      if (el.closest('aside.notes') || (!document.body.classList.contains('is-export') && el.closest('.fragment:not(.visible)'))) continue;
      const style = getComputedStyle(el), rect = el.getBoundingClientRect();
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0 || !rect.width || !rect.height) continue;
      if (rect.left < bounds.left - 2 || rect.top < bounds.top - 2 || rect.right > bounds.right + 2 || rect.bottom > bounds.bottom + 2) {
        offenders.push({ tag: el.tagName, id: el.id || null, text: el.textContent.trim().slice(0, 70) });
      }
    }
    return { hasOverflow: slide.scrollHeight > slide.clientHeight + 2 || slide.scrollWidth > slide.clientWidth + 2 || offenders.length > 0,
      offenders: offenders.slice(0, 15), width: slide.clientWidth, height: slide.clientHeight, scrollWidth: slide.scrollWidth, scrollHeight: slide.scrollHeight };
  });
}
module.exports = { open, visit, overflow };
