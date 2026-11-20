#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const cheerio = require('cheerio');
const { main: create } = require('./create-presentation');
const { args, write, escape, digest } = require('./lib');
function svg(body, width = 900, height = 400) { return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img"><style>text{font-family:Arial,'PingFang SC',sans-serif;fill:#172b3a} .box{fill:#eaf0f5;stroke:#24577a;stroke-width:2}</style>${body}</svg>`; }
function demo(out) {
  if (fs.existsSync(out) && fs.readdirSync(out).length) throw new Error('Demo output directory must be empty');
  fs.mkdirSync(path.join(out, 'assets'), { recursive: true });
  const save = (name, data) => write(path.join(out, 'assets', name), data);
  const pipeline = svg(`<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8" fill="#24577a"/></marker></defs>${['音频输入', '编码与聚合', '预测与核查'].map((t, i) => `<rect class="box" x="${25 + i * 300}" y="120" width="250" height="100" rx="8"/><text x="${150 + i * 300}" y="180" text-anchor="middle" font-size="30">${t}</text>${i < 2 ? `<path d="M${275 + i * 300},170 h50" stroke="#24577a" stroke-width="3" marker-end="url(#arrow)"/>` : ''}`).join('')}<text x="450" y="300" text-anchor="middle" font-size="24">解释数据怎样流动；此图不表示机制已经得到验证。</text>`);
  save('pipeline.svg', pipeline);
  const question = svg(`<text x="450" y="58" text-anchor="middle" font-size="32">相同总指标，可能对应不同样本变化</text>${['短样本', '长样本'].map((t, i) => `<rect class="box" x="${70 + i * 430}" y="110" width="330" height="160" rx="10"/><text x="${235 + i * 430}" y="170" text-anchor="middle" font-size="30">${t}</text><text x="${235 + i * 430}" y="225" text-anchor="middle" font-size="26">分开观察，再核条件</text>`).join('')}<text x="450" y="345" text-anchor="middle" font-size="22">教学示意，非项目发现</text>`);
  save('question.svg', question);
  const threshold = svg([0.2, 0.5, 0.8].map((t, i) => { const scores = [0.1, 0.3, 0.6, 0.9]; return `<text x="20" y="${70 + i * 115}" font-size="26">阈值 ${t}</text>${scores.map((s, j) => `<circle cx="${300 + j * 130}" cy="${60 + i * 115}" r="25" fill="${s >= t ? '#24577a' : '#dce2e7'}"/><text x="${300 + j * 130}" y="${65 + i * 115}" text-anchor="middle" fill="${s >= t ? '#fff' : '#172b3a'}" style="fill:${s >= t ? '#fff' : '#172b3a'}" font-size="19">${s}</text>`).join('')}`; }).join(''));
  save('threshold.svg', threshold);
  const signal = Array.from({ length: 16000 }, (_, i) => Math.sin(2 * Math.PI * 440 * i / 16000));
  const envelope = Array.from({ length: 400 }, (_, i) => {
    const values = signal.slice(i * 40, (i + 1) * 40);
    return `<line x1="${30 + i * 835 / 399}" x2="${30 + i * 835 / 399}" y1="${105 - 30 * Math.max(...values)}" y2="${105 - 30 * Math.min(...values)}" stroke="#24577a" stroke-width="2"/>`;
  }).join('');
  const wave = signal.slice(0, 320).map((value, i) => `${30 + i * 835 / 319},${240 - 36 * value}`).join(' ');
  const waveform = svg(`<text x="450" y="32" text-anchor="middle" font-size="25">合成音频：1秒概览与前20ms局部波形</text>${envelope}<line id="playhead" x1="30" x2="30" y1="60" y2="145" stroke="#a04c37" stroke-width="4"/><text x="30" y="175" font-size="21">0s</text><text x="865" y="175" text-anchor="end" font-size="21">1s（每窗幅度范围）</text><polyline points="${wave}" fill="none" stroke="#24577a" stroke-width="2.5"/><text x="30" y="310" font-size="21">0ms</text><text x="865" y="310" text-anchor="end" font-size="21">20ms（实际合成样本）</text>`, 900, 340);
  save('waveform.svg', waveform);
  const samples = 16000, audio = Buffer.alloc(44 + samples * 2); audio.write('RIFF'); audio.writeUInt32LE(36 + samples * 2, 4); audio.write('WAVEfmt ', 8); audio.writeUInt32LE(16, 16); audio.writeUInt16LE(1, 20); audio.writeUInt16LE(1, 22); audio.writeUInt32LE(16000, 24); audio.writeUInt32LE(32000, 28); audio.writeUInt16LE(2, 32); audio.writeUInt16LE(16, 34); audio.write('data', 36); audio.writeUInt32LE(samples * 2, 40);
  for (let i = 0; i < samples; i++) audio.writeInt16LE(Math.round(6000 * Math.sin(2 * Math.PI * 440 * i / 16000)), 44 + i * 2);
  save('tone.wav', audio);
  const data = { label: '教学示例，非项目实测', groups: ['短样本', '长样本'], baseline: [6, 10], method: [8, 8], scores: [0.1, 0.3, 0.6, 0.9] };
  save('example.json', JSON.stringify(data, null, 2));
  save('pipeline.mmd', 'flowchart LR\n A[先前判断] --> B[本轮观察]\n B --> C[判断变化]\n C --> D[后续取证]\n');
  const chart = JSON.stringify({ data: { labels: data.groups, datasets: [{ label: '示例A', data: data.baseline, backgroundColor: '#24577a' }, { label: '示例B', data: data.method, backgroundColor: '#a04c37' }] }, options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: '示例错误率（%）', font: { size: 20 } }, ticks: { font: { size: 20 } } }, x: { ticks: { font: { size: 20 } } } }, plugins: { legend: { labels: { font: { size: 20 } } } } } });
  const image = (id, file, alt) => `<figure><div class="visual"><img data-asset-id="${id}" src="assets/${file}" alt="${alt}"></div><figcaption>教学示意，非项目实测。</figcaption></figure>`;
  const page = (id, title, content, notes) => `<section id="${id}"><h2>${title}</h2><div class="content">${content}</div><p class="footnote">示例报告 · 所有数据与机制图仅用于展示汇报表达方式</p><aside class="notes">${notes}</aside></section>`;
  const definitions = [
    ['question', '总指标是否掩盖了不同样本的变化？', image('question-map', 'question.svg', '短样本与长样本需要分别观察'), '先恢复问题，再说明当前需要什么证据。'],
    ['method', '先看整体，再解释每个处理步骤', `<div style="display:grid;grid-template-rows:minmax(0,1fr) auto;flex:1;min-height:0">${image('method-map', 'pipeline.svg', '输入、编码聚合、预测核查的流程')}<div style="display:flex;gap:24px"><p class="fragment">先说明输入、输出及约束。</p><p class="fragment">再解释最关键的处理关系。</p></div></div>`, '图是输入输出的说明，不是机制证据。逐步显示只是控制解释顺序。'],
    ['results', '同一总量也可能包含相反的分组变化', `<div class="chart-container" data-asset-id="example-data"><canvas data-chart="bar" aria-label="两组教学数据的对比" role="img"><!--${chart}--></canvas></div><p>示例A与B的两组均值相同；分组方向却不同。</p>`, '先讲横轴与单位，再比较对应分组；这些数值不来自实际研究。'],
    ['threshold', '滑块展示阈值如何改变保留的示例样本', `<div class="live-only" data-interactive data-static-fallback="threshold-static"><label for="threshold-control">教学阈值</label> <input id="threshold-control" type="range" min="0" max="1" step="0.1" value="0.5"> <button id="reset-threshold">重置</button><p id="threshold-output"></p><svg viewBox="0 0 900 170" role="img" aria-label="被保留的教学样本">${data.scores.map((s, i) => `<circle data-score="${s}" cx="${130 + i * 190}" cy="80" r="35"/><text x="${130 + i * 190}" y="145" text-anchor="middle" font-size="26">${s}</text>`).join('')}</svg></div><div id="threshold-static" class="export-only static-figure">${image('threshold-cases', 'threshold.svg', '阈值0.2、0.5、0.8对应的保留样本')}</div><p>仅改变四个给定分数的筛选，不模拟真实模型性能。</p>`, '演示0.2、0.5、0.8并重置。PDF列出同样的关键状态。'],
    ['audio', '把听到的片段对应到可见的时间位置', `<div data-asset-id="waveform" style="flex:1;min-height:0">${waveform}</div><audio id="demo-audio" controls preload="metadata" src="assets/tone.wav" data-static-fallback="audio-static" data-asset-id="tone"></audio><div id="audio-static" class="export-only"><p>静态页保留波形与条件：440Hz合成正弦，16kHz采样，1秒；不可据此评价音质。</p></div>`, '本地合成音频仅用于验证媒体控制。点击播放时，时间线标记随进度变化。'],
    ['code', '说明每个量，再把公式对应到代码', `<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:28px;flex:1;min-height:0"><div><p>给定样本分数 sᵢ 与阈值 τ：</p><p>$$n(\\tau)=\\sum_i \\mathbf{1}[s_i\\geq\\tau]$$</p><p>n 表示保留数量；不表示准确率。</p></div><div class="code-block"><pre><code class="language-python" data-trim data-line-numbers="1|2-4">${escape('scores = [0.1, 0.3, 0.6, 0.9]\nthreshold = 0.5\nkeep = [s >= threshold for s in scores]\ncount = sum(keep)')}</code></pre><p style="color:#d4e1eb;font-size:17pt">示例输出 count = 2</p></div></div>`, '公式和输出针对同一教学例子；并未执行训练或真实项目评测。'],
    ['discussion', '下一步应取得什么能区分解释的证据？', `${image('question-map', 'question.svg', '分别核对分组和条件')}<p>讨论：优先核查测量/条件差异，还是安排新的受控比较？</p>`, '把两个选项所减少的未知及成本讲清，保留原因未知的可能。'],
    ['appendix', '附录：汇报怎样对应研究判断', `<div class="mermaid" data-asset-id="research-flow" style="flex:1;min-height:0">flowchart LR\n A[先前判断] --> B[本轮观察]\n B --> C[判断变化]\n C --> D[后续取证]</div><p>图中箭头表示记录顺序，不是自动研究裁决。</p>`, '此页是解释流程的附录，不计入主报告预算。']
  ];
  const files = [['question-map', 'question.svg'], ['method-map', 'pipeline.svg'], ['example-data', 'example.json'], ['threshold-cases', 'threshold.svg'], ['waveform', 'waveform.svg'], ['tone', 'tone.wav'], ['research-flow', 'pipeline.mmd']];
  const ids = [['question-map'], ['method-map'], ['example-data'], ['threshold-cases'], ['waveform', 'tone'], [], ['question-map'], ['research-flow']];
  const kinds = ['diagram', 'diagram', 'plot', 'interaction', 'media', 'text', 'diagram', 'diagram'];
  const plan = { schema_version: 1, title: '让听众看见问题、依据与未知', scenario: 'group_meeting', audience: '同组研究者', goal: '展示内容组织与视觉表达，不报告真实研究结论', talk_minutes: 8,
    sources: [{ id: 'demo', ref: 'assets/example.json：人为构造的教学例子；非项目实测' }],
    assets: files.map(([id, file]) => ({ id, file: `assets/${file}`, purpose: '帮助理解本页明确的信息', alt: '带标注的教学素材', status: 'ready', source: { kind: 'example', ref: 'create-demo.js中的确定性教学构造' }, label: '教学示例，非实测', sha256: digest(fs.readFileSync(path.join(out, 'assets', file))) })),
    slides: definitions.map(([id, title, , notes], i) => ({ id, title, question: title, message: notes, notes, role: id === 'appendix' ? 'appendix' : 'main', seconds: 45, evidence_ids: ['demo'], visual: { kind: kinds[i], purpose: notes, asset_ids: ids[i], ...(i === 3 ? { fallback_id: 'threshold-static' } : {}), ...(i === 4 ? { fallback_id: 'audio-static' } : {}), ...(i === 5 ? { text_only_reason: '本页解释公式与具体代码，额外配图不能替代符号/计算的对应说明' } : {}) } })) };
  const planPath = path.join(out, 'talk.plan.json'); write(planPath, JSON.stringify(plan, null, 2));
  const html = path.join(out, 'talk.html');
  create(['--plan', planPath, '--features', 'charts,math,code,mermaid', '--title', plan.title, '--output', html]);
  const $ = cheerio.load(fs.readFileSync(html, 'utf8')); $('.slides').html(definitions.map(([id, title, content, notes]) => page(id, title, content, notes)).join('\n'));
  let source = $.html();
  const interaction = `<script>
const threshold=document.getElementById('threshold-control');
function updateThreshold(){const t=Number(threshold.value);let kept=0;document.querySelectorAll('[data-score]').forEach(el=>{const keep=Number(el.dataset.score)>=t;el.setAttribute('fill',keep?'#24577a':'#dce2e7');if(keep)kept++;});document.getElementById('threshold-output').textContent='阈值 '+t.toFixed(1)+'；保留 '+kept+' / 4 个教学样本';}
threshold.addEventListener('input',updateThreshold);document.getElementById('reset-threshold').onclick=()=>{threshold.value='0.5';updateThreshold();};updateThreshold();
const audio=document.getElementById('demo-audio');audio.addEventListener('timeupdate',()=>{const x=30+835*(audio.currentTime/(audio.duration||1));const line=document.getElementById('playhead');line.setAttribute('x1',x);line.setAttribute('x2',x);});
</script>`;
  source = source.replace('<script>Presentation.start(', interaction + '<script>Presentation.start(');
  write(html, source, true);
  return { html, plan: planPath };
}
if (require.main === module) { try { const o = args(process.argv.slice(2), ['out']); if (!o.out) throw new Error('Usage: node create-demo.js --out empty-directory'); console.log(JSON.stringify(demo(path.resolve(o.out)))); } catch (e) { console.error(e.message); process.exitCode = 1; } }
module.exports = { demo };
