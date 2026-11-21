#!/usr/bin/env node

/**
 * revealjs-pro · 动态主题生成
 * 输入: --primary <hex> --mode <light|dark> --font-pairing <academic|modern|mono-heavy> --output <styles.css>
 * 输出: 直接写 styles.css（三层 token: primitive → semantic → component）+ WCAG 对比度校验报告
 *
 * 设计: agent 做判断（从内容定主色/mode/字体），脚本做派生（辅色/强调/callout/代码块/中性/文字 + 校验）
 */

const fs = require('fs');
const path = require('path');

// --- 参数解析 ---
const args = process.argv.slice(2);
function arg(name, dflt) {
  const i = args.indexOf('--' + name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : dflt;
}
const primary = arg('primary', '#1C2833');
const mode = arg('mode', 'light');                    // light | dark
const fontPairing = arg('font-pairing', 'modern');    // academic | modern | mono-heavy
const out = arg('output', 'styles.css');

// --- 颜色工具: hex <-> HSL ---
function hexToHsl(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  const r = parseInt(hex.slice(0, 2), 16) / 255;
  const g = parseInt(hex.slice(2, 4), 16) / 255;
  const b = parseInt(hex.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) { h = s = 0; }
  else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return [h * 360, s * 100, l * 100];
}
function hslToHex(h, s, l) {
  h /= 360; s /= 100; l /= 100;
  let r, g, b;
  if (s === 0) { r = g = b = l; }
  else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3); g = hue2rgb(p, q, h); b = hue2rgb(p, q, h - 1 / 3);
  }
  const toHex = x => Math.round(x * 255).toString(16).padStart(2, '0');
  return '#' + toHex(r) + toHex(g) + toHex(b);
}

// --- WCAG 对比度 ---
function hexToRgb(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
}
function relLum(hex) {
  const [rs, gs, bs] = hexToRgb(hex);
  const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(rs) + 0.7152 * f(gs) + 0.0722 * f(bs);
}
function contrast(a, b) {
  const la = relLum(a), lb = relLum(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
// 调 hex 的亮度 l 到对 bg 对比度 >= target，保留色相、取最接近原亮度的（避免变纯黑丢色相）
function adjustForContrast(hex, bg, target) {
  const [h, s, origL] = hexToHsl(hex);
  let best = null, bestDist = Infinity;
  for (let tryL = 0; tryL <= 100; tryL += 5) {
    const candidate = hslToHex(h, s, tryL);
    if (contrast(candidate, bg) >= target) {
      const dist = Math.abs(tryL - origL);
      if (dist < bestDist) { best = candidate; bestDist = dist; }
    }
  }
  return best || hex;  // 没有过 target 的，返回原色
}

// --- 派生逻辑 ---
const [h, s, l] = hexToHsl(primary);
const background = mode === 'dark' ? '#1a1a2e' : '#ffffff';
const secondary = adjustForContrast(hslToHex((h + 30) % 360, Math.min(s, 50), Math.max(l, 25)), background, 4.5);
const accent = adjustForContrast(hslToHex((h + 180) % 360, Math.min(s + 20, 80), 45), background, 4.5);  // 互补强调，自动调对比度
const calloutBg = hslToHex(h, Math.min(s, 30), mode === 'dark' ? 20 : 95);           // 主色浅变体
const codeBg = mode === 'dark' ? '#1e1e1e' : '#282c34';                              // neutral 深底
const textColor = mode === 'dark' ? '#f0f0f0' : '#222222';
const mutedColor = mode === 'dark' ? '#999999' : '#666666';
const boxBg = mode === 'dark' ? '#252540' : '#f5f5f5';
const boxBorder = mode === 'dark' ? '#3a3a5c' : '#dddddd';

// --- 字体配对 ---
const fonts = {
  academic:    { heading: '"Source Serif Pro", Georgia, serif', body: '"Source Sans Pro", Helvetica, sans-serif' },
  modern:      { heading: '"Source Sans Pro", Helvetica, sans-serif', body: '"Source Sans Pro", Helvetica, sans-serif' },
  'mono-heavy':{ heading: '"JetBrains Mono", monospace', body: '"Inter", Helvetica, sans-serif' },
};
const fp = fonts[fontPairing] || fonts.modern;
const highlightTheme = mode === 'dark' ? 'monokai-sublime' : 'github';

function check(name, fg, bg) {
  const r = contrast(fg, bg);
  const ok = r >= 4.5;
  console.log(`  ${ok ? '✅' : '❌'} ${name}: ${fg} on ${bg} = ${r.toFixed(1)}:1${ok ? '' : ' (<4.5, 调主色或 mode)'}`);
  return ok;
}

// --- 生成 CSS: 读 base-styles.css 作基底，替换 :root 为生成的 token，保留所有样式规则 ---
const baseStylesPath = path.join(__dirname, '..', 'references', 'base-styles.css');
let baseCss = '';
try { baseCss = fs.readFileSync(baseStylesPath, 'utf8'); } catch(e) {}

const rootBlock = `:root {
  /* === primitive (raw) === */
  --color-primary:   ${primary};
  --color-secondary: ${secondary};
  --color-accent:    ${accent};

  /* === semantic === */
  --background-color: ${background};
  --section-divider-bg: ${background};
  --text-color:      ${textColor};
  --muted-color:     ${mutedColor};
  --line-color:      ${mutedColor};
  --box-bg:          ${boxBg};
  --box-border:      ${boxBorder};

  /* typography - ALWAYS pt */
  --heading-font: ${fp.heading};
  --body-font:    ${fp.body};
  --base-font-size: 32px;
  --text-size: 16pt;
  --h1-size: 48pt;
  --h2-size: 36pt;
  --h3-size: 24pt;
  --footnote-size: 11pt;

  /* layout */
  --slide-padding: 60px;
  --slide-padding-top: 40px;
  --content-gap: 30px;
  --box-radius: 8px;

  /* === component === */
  --callout-bg:      ${calloutBg};
  --callout-border:  ${primary};
  --stat-card-bg:    ${boxBg};
  --feature-card-bg: ${boxBg};
  --code-bg:         ${codeBg};
  --blockquote-border: ${primary};
}`;

// 替换 base-styles.css 的 :root {...} 块为生成的 token，保留其他所有样式规则
let css;
if (baseCss && /:root\s*\{/.test(baseCss)) {
  css = baseCss.replace(/:root\s*\{[^}]*\}/, rootBlock);
} else {
  css = rootBlock;  // 找不到 base-styles.css，退化成只写 :root
}
css = `/* Auto-generated by generate-theme.js | primary=${primary} mode=${mode} font=${fontPairing} highlight=${highlightTheme} */
/* highlight.js 主题建议: https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/${highlightTheme}.min.css */
` + css;

fs.writeFileSync(out, css);

// --- 校验报告 ---
console.log(`\n生成主题 → ${out}`);
console.log(`主色=${primary} | mode=${mode} | 字体=${fontPairing} | highlight 主题=${highlightTheme}`);
console.log('对比度校验 (WCAG 4.5:1):');
check('正文', textColor, background);
check('主色标题', primary, background);
check('强调色', accent, background);
check('辅色', secondary, background);
check('callout 文字', textColor, calloutBg);
check('代码文字', '#abb2bf', codeBg);
console.log(`\n提示: 把 HTML 里 <link id="highlight-theme"> 的 href 改成 highlight.js@11.9.0/styles/${highlightTheme}.min.css 以匹配 ${mode} 模式`);
