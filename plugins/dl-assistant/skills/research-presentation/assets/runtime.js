/* Research presentation runtime; local assets, explicit readiness and static export. */
(function (global) {
  'use strict';
  function csv(text) {
    const rows = []; let row = [], field = '', quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '"') { if (quoted && text[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted; }
      else if (c === ',' && !quoted) { row.push(field); field = ''; }
      else if ((c === '\n' || c === '\r') && !quoted) {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(field); if (row.some(x => x.trim())) rows.push(row); row = []; field = '';
      } else field += c;
    }
    if (quoted) throw new Error('Unclosed CSV quote');
    row.push(field); if (row.some(x => x.trim())) rows.push(row);
    if (rows.length < 2 || rows[0].length < 2 || rows.some(r => r.length !== rows[0].length)) throw new Error('CSV needs rectangular label/value columns');
    const number = x => { if (!x.trim()) return null; const n = Number(x); if (!Number.isFinite(n)) throw new Error('CSV chart value must be finite'); return n; };
    return { data: { labels: rows.slice(1).map(r => r[0]), datasets: rows[0].slice(1).map((label, j) => ({ label, data: rows.slice(1).map(r => number(r[j + 1])) })) }, options: { maintainAspectRatio: false } };
  }
  function chartConfig(text) { return text.trim().startsWith('{') ? JSON.parse(text) : csv(text); }
  if (typeof module !== 'undefined' && module.exports) { module.exports = { csv, chartConfig }; return; }
  const tasks = [];
  const exportMode = new URLSearchParams(location.search).has('export');
  const Presentation = global.Presentation = {
    register(task) { tasks.push(task); },
    csv, chartConfig,
    async start(options = {}) {
      document.body.classList.toggle('is-export', exportMode);
      global.presentationErrors = [];
      Reveal.on('pdf-ready', () => { global.presentationPdfReady = true; });
      const diagramSources = Array.from(document.querySelectorAll('.mermaid')).map(node => [node, node.textContent]);
      if (global.mermaid) mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral', flowchart: { htmlLabels: false }, themeVariables: { fontSize: '26px', fontFamily: 'Arial, sans-serif' } });
      global.presentationReady = (async () => {
        await Reveal.initialize({ width: 1280, height: 720, margin: 0.02, center: false, hash: true, transition: exportMode ? 'none' : 'slide',
          controls: !exportMode, progress: !exportMode, slideNumber: 'c/t', autoPlayMedia: false, pdfSeparateFragments: false, pdfMaxPagesPerSlide: 1, ...options });
        if (global.renderMathInElement) renderMathInElement(document.querySelector('.slides'), {
          delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }], throwOnError: true,
          errorCallback: (message, error) => { throw error; }
        });
        if (document.querySelector('.mermaid')) {
          if (!global.mermaid) throw new Error('Enable --features mermaid before using Mermaid');
          let index = 0;
          for (const [node, source] of diagramSources) {
            const host = document.createElement('div');
            host.style.cssText = 'position:absolute;left:-20000px;top:0;width:1100px;visibility:hidden';
            document.body.appendChild(host);
            try { const result = await mermaid.render('research-diagram-' + index++, source, host); node.innerHTML = result.svg; node.dataset.processed = 'true'; }
            finally { host.remove(); }
          }
        }
        if (global.Chart) {
          const theme = getComputedStyle(document.documentElement);
          Chart.defaults.color = theme.getPropertyValue('--text-color').trim() || '#172b3a';
          Chart.defaults.borderColor = theme.getPropertyValue('--box-border').trim() || '#bcc9d2';
          Chart.defaults.font.family = theme.getPropertyValue('--body-font').trim() || 'sans-serif';
          Chart.defaults.font.size = 20;
        }
        for (const canvas of document.querySelectorAll('canvas[data-chart]')) {
          if (!global.Chart) throw new Error('Enable --features charts before using charts');
          let text;
          if (canvas.dataset.chartSrc) {
            const url = new URL(canvas.dataset.chartSrc, location.href);
            if (url.origin !== location.origin) throw new Error('Chart data must be local');
            const response = await fetch(url); if (!response.ok) throw new Error('Chart data unavailable'); text = await response.text();
          } else text = canvas.innerHTML.match(/<!--[\s\S]*?-->/)?.[0].slice(4, -3) || '';
          const config = chartConfig(text);
          new Chart(canvas, { ...config, type: canvas.dataset.chart, options: { ...config.options, animation: exportMode ? false : config.options?.animation, responsive: true, maintainAspectRatio: false } });
        }
        for (const task of tasks) await (typeof task === 'function' ? task() : task);
        for (const img of document.querySelectorAll('img[data-src]')) { if (!img.getAttribute('src')) img.src = img.dataset.src; }
        for (const widget of document.querySelectorAll('[data-interactive],video,audio,iframe')) { if (exportMode) widget.classList.add('live-only'); }
        await document.fonts.ready;
        await Promise.all(Array.from(document.images).map(img => img.decode().catch(() => { throw new Error(`Image unavailable: ${img.getAttribute('src')}`); })));
        Reveal.layout();
        global.presentationSettled = true;
      })().catch(error => { global.presentationErrors.push(String(error.message).slice(0, 1000)); global.presentationSettled = true; console.error(error); });
      return global.presentationReady;
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
