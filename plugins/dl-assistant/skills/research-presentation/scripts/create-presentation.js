#!/usr/bin/env node

/**
 * Creates a reveal.js presentation scaffold with the specified options.
 * Usage: node create-presentation.js [options]
 *
 * revealjs-pro: scaffold 全局引入 highlight.js / KaTeX / mermaid / qrcode.js
 */

const fs = require('fs');
const path = require('path');

const BASE_STYLES_PATH = path.join(__dirname, '..', 'references', 'base-styles.css');

function parseArgs(args) {
  const options = {
    slides: null,
    structure: null,
    output: 'presentation.html',
    title: 'Presentation',
    stylesFile: 'styles.css',
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--slides' || arg === '-s') {
      options.slides = parseInt(args[++i], 10);
    } else if (arg === '--structure') {
      options.structure = args[++i].split(',').map(n => n === 'd' ? 'd' : parseInt(n, 10));
    } else if (arg === '--output' || arg === '-o') {
      options.output = args[++i];
    } else if (arg === '--title') {
      options.title = args[++i];
    } else if (arg === '--styles') {
      options.stylesFile = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  return options;
}

function printHelp() {
  console.log(`
create-presentation.js - Generate a reveal.js presentation scaffold (revealjs-pro)

Usage: node create-presentation.js [options]

Options:
  --slides, -s <num>    Number of horizontal slides (simple mode)
  --structure <list>    Mixed layout: comma-separated values (e.g., "1,1,d,3,1,d,1")
  --output, -o <file>   Output HTML filename (default: presentation.html)
  --title <text>        Presentation title (default: Presentation)
  --styles <file>       Custom CSS filename (default: styles.css)
  --help, -h            Show this help message

Scaffold 全局引入: reveal.js / Chart.js / Font Awesome / highlight.js / KaTeX / mermaid / qrcode.js
按需库（d3/iconify/plotly/diff2html/rough.js/leaflet/anime.js/countUp.js/medium-zoom）不全局引，
用时在该页 <script> 引，见对应 reference 文档。
`);
}

function generateSlides(structure) {
  let slides = '';
  let hIndex = 1;
  let dividerCount = 1;

  for (let colIndex = 0; colIndex < structure.length; colIndex++) {
    const item = structure[colIndex];

    if (item === 'd') {
      slides += `
      <section id="divider-${dividerCount}" class="section-divider" data-state="is-section-divider">
        <h1>Section ${dividerCount} Title</h1>
      </section>
`;
      dividerCount++;
      hIndex++;
    } else if (item === 1) {
      if (hIndex === 1) {
        slides += `
      <section id="title" class="section-divider" data-state="is-section-divider">
        <h1>Presentation Title</h1>
      </section>
`;
      } else {
        slides += `
      <section id="slide-${hIndex}">
        <h2>Slide ${hIndex} Title Here</h2>
      </section>
`;
      }
      hIndex++;
    } else {
      slides += `
      <section>
`;
      for (let vIndex = 1; vIndex <= item; vIndex++) {
        slides += `        <section id="slide-${hIndex}-${vIndex}">
          <h2>Slide ${hIndex}.${vIndex} Title Here</h2>
        </section>
`;
      }
      slides += `      </section>
`;
      hIndex++;
    }
  }

  return slides;
}

function generateHTML(options) {
  const slidesContent = generateSlides(options.structure);

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${options.title}</title>

  <!-- Reveal.js core -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">

  <!-- Font Awesome for icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

  <!-- Custom styles -->
  <link rel="stylesheet" href="${options.stylesFile}">

  <!-- Chart.js for data visualization -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <!-- highlight.js 代码高亮（主题由 generate-theme.js 按 mode 切换 #highlight-theme href）-->
  <link rel="stylesheet" id="highlight-theme" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css">
  <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/common.min.js"></script>

  <!-- KaTeX 数学公式 -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

  <!-- mermaid 图 -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>

  <!-- qrcode 二维码 -->
  <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
</head>
<body>
  <div class="reveal">
    <div class="slides">
${slidesContent}
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js-plugins@latest/chart/plugin.js"></script>
  <script>
    // mermaid 初始化（不自动启动，slidechanged 时按需渲染当前页）
    mermaid.initialize({ startOnLoad: false, theme: 'default' });

    // KaTeX 渲染辅助：渲染指定 root 内的 $...$ / $$...$$
    function renderMath(root) {
      if (window.renderMathInElement) {
        renderMathInElement(root, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
          ],
          throwOnError: false
        });
      }
    }

    // mermaid 渲染：预渲染所有页的 .mermaid 块（decktape 截图时异步渲染会漏，ready 时全渲染）
    function renderAllMermaid() {
      const nodes = document.querySelectorAll('.mermaid:not([data-processed])');
      nodes.forEach(el => el.setAttribute('data-processed', 'true'));
      if (nodes.length) try { mermaid.run({ nodes: Array.from(nodes) }); } catch(e) {}
    }
    function renderMermaid(slide) {
      if (!slide) return;
      const nodes = slide.querySelectorAll('.mermaid:not([data-processed])');
      nodes.forEach(el => el.setAttribute('data-processed', 'true'));
      if (nodes.length) try { mermaid.run({ nodes: Array.from(nodes) }); } catch(e) {}
    }

    Reveal.initialize({
      width: 1280,
      height: 720,
      margin: 0,
      controls: true,
      progress: true,
      slideNumber: false,
      hash: true,
      transition: 'slide',
      center: false,
      plugins: [ RevealChart, RevealHighlight ],
      chart: {
        defaults: Object.assign({
          color: 'rgba(0, 0, 0, 0.8)',
          borderColor: 'rgba(0, 0, 0, 0.8)',
          devicePixelRatio: 2
        }, window.location.search.includes('export') ? { animation: false } : {})
      }
    });

    // 渲染公式 + mermaid（ready 时全渲染，slidechanged 时渲染当前页）
    Reveal.on('ready', () => {
      renderMath(document.body);
      renderAllMermaid();
    });
    Reveal.on('slidechanged', (e) => {
      renderMath(e.currentSlide); renderMermaid(e.currentSlide);
    });
  </script>
</body>
</html>
`;
}

function main() {
  const args = process.argv.slice(2);
  const options = parseArgs(args);

  if (options.slides !== null && options.structure !== null) {
    console.error('Error: Cannot use both --slides and --structure. Choose one.');
    process.exit(1);
  }

  if (options.slides === null && options.structure === null) {
    options.structure = [1, 1, 1, 1, 1];
  } else if (options.slides !== null) {
    if (options.slides < 1 || isNaN(options.slides)) {
      console.error('Error: Slide count must be at least 1.');
      process.exit(1);
    }
    options.structure = Array(options.slides).fill(1);
  } else {
    if (options.structure.some(n => n !== 'd' && (n < 1 || isNaN(n)))) {
      console.error('Error: Structure values must be positive integers or "d" for dividers.');
      process.exit(1);
    }
  }

  const totalSlides = options.structure.reduce((a, b) => a + (b === 'd' ? 1 : b), 0);
  const outputDir = path.dirname(options.output);

  if (outputDir && outputDir !== '.') {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const html = generateHTML(options);
  fs.writeFileSync(options.output, html);
  console.log(`Created ${options.output}`);

  const stylesOutputPath = outputDir && outputDir !== '.'
    ? path.join(outputDir, options.stylesFile)
    : options.stylesFile;

  if (!fs.existsSync(stylesOutputPath)) {
    if (fs.existsSync(BASE_STYLES_PATH)) {
      fs.copyFileSync(BASE_STYLES_PATH, stylesOutputPath);
      console.log(`Copied base-styles.css to ${stylesOutputPath}`);
    } else {
      console.warn(`Warning: Could not find ${BASE_STYLES_PATH}`);
    }
  } else {
    console.log(`${stylesOutputPath} already exists, skipping`);
  }

  console.log(`\nPresentation created with ${totalSlides} slides (structure: ${options.structure.join(',')}).`);
  console.log(`Run generate-theme.js to generate styles.css, then open ${options.output} in a browser.`);
}

main();
