/** revealjs-pro · 检查 reveal.js slides 内容溢出
 *  用 puppeteer，含 headless-shell 回退（修原 skill full chrome 启动失败问题）
 */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const os = require('os');

// 启动浏览器：先试 full chrome（PUPPETEER_EXECUTABLE_PATH env 优先），失败回退 headless-shell
async function launchBrowser() {
  // 1. 先试默认 full chrome
  try {
    const browser = await puppeteer.launch({
      headless: true,
      timeout: 10000,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
    });
    const page = await browser.newPage();
    await page.goto('about:blank');  // 验证真能用（full chrome framework 缺时 launch 成功但 goto 崩）
    return { browser, page, fallback: false };
  } catch (e) {
    const msg = (e.message || '').split('\n')[0];
    console.warn(`⚠️  full chrome 启动失败（${msg}），尝试回退 headless-shell...`);
  }
  // 2. 找 headless-shell
  const shellDir = path.join(os.homedir(), '.cache/puppeteer/chrome-headless-shell');
  let shellBin = null;
  if (fs.existsSync(shellDir)) {
    for (const d of fs.readdirSync(shellDir)) {
      const candidates = [
        path.join(shellDir, d, 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell'),
        path.join(shellDir, d, 'chrome-headless-shell-mac-x64', 'chrome-headless-shell'),
        path.join(shellDir, d, 'chrome-linux64', 'chrome-headless-shell'),
        path.join(shellDir, d, 'chrome-win64', 'chrome-headless-shell.exe'),
      ];
      for (const c of candidates) {
        if (fs.existsSync(c)) { shellBin = c; break; }
      }
      if (shellBin) break;
    }
  }
  if (!shellBin) {
    throw new Error('headless-shell 也没找到。修复：跑 `npx puppeteer browsers install chrome-headless-shell`，或手动设 PUPPETEER_EXECUTABLE_PATH 指向可用 chrome');
  }
  console.warn(`   回退到: ${shellBin}`);
  const browser = await puppeteer.launch({ headless: true, executablePath: shellBin });
  const page = await browser.newPage();
  return { browser, page, fallback: true };
}

async function checkSlideOverflow(htmlPath) {
  const absolutePath = path.resolve(htmlPath);
  const fileUrl = `file://${absolutePath}`;

  const { browser, page, fallback } = await launchBrowser();
  if (fallback) console.log('（使用 headless-shell 回退模式）\n');

  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => typeof Reveal !== 'undefined' && Reveal.isReady());

  const results = await page.evaluate(() => {
    const allSlides = document.querySelectorAll('.slides > section, .slides > section > section');
    const slides = [];
    allSlides.forEach((slide, i) => {
      const isStackParent = slide.parentElement.classList.contains('slides') && slide.querySelector('section');
      if (isStackParent) return;
      const id = slide.id || `slide-${i}`;
      const scrollHeight = slide.scrollHeight;
      const scrollWidth = slide.scrollWidth;
      const clientHeight = slide.clientHeight;
      const clientWidth = slide.clientWidth;
      const hasVerticalOverflow = scrollHeight > clientHeight;
      const hasHorizontalOverflow = scrollWidth > clientWidth;
      slides.push({
        index: i, id,
        hasOverflow: hasVerticalOverflow || hasHorizontalOverflow,
        hasVerticalOverflow, hasHorizontalOverflow,
        dimensions: { scrollHeight, clientHeight, scrollWidth, clientWidth,
          verticalDiff: scrollHeight - clientHeight, horizontalDiff: scrollWidth - clientWidth }
      });
    });
    return slides;
  });

  await browser.close();
  return results;
}

async function main() {
  const htmlPath = process.argv[2];
  if (!htmlPath) {
    console.error('Usage: node check-overflow.js <path-to-html>');
    process.exit(1);
  }
  console.log(`Checking slides for overflow: ${htmlPath}\n`);
  const results = await checkSlideOverflow(htmlPath);
  let hasAnyOverflow = false;
  for (const slide of results) {
    if (slide.hasOverflow) {
      hasAnyOverflow = true;
      console.log(`OVERFLOW: Slide ${slide.index} (${slide.id})`);
      if (slide.hasVerticalOverflow)
        console.log(`  - Vertical: ${slide.dimensions.verticalDiff}px (content ${slide.dimensions.scrollHeight}, container ${slide.dimensions.clientHeight})`);
      if (slide.hasHorizontalOverflow)
        console.log(`  - Horizontal: ${slide.dimensions.horizontalDiff}px (content ${slide.dimensions.scrollWidth}, container ${slide.dimensions.clientWidth})`);
    }
  }
  if (!hasAnyOverflow) console.log('No overflow detected on any slides.');
  console.log(`\nTotal slides checked: ${results.length}`);
}

main().catch(err => { console.error('Error:', err); process.exit(1); });
