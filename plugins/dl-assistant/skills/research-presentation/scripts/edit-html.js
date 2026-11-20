#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const cheerio = require('cheerio');
const { args, digest, escape, write, staticFile } = require('./lib');
function editable(source) {
  const $ = cheerio.load(source, { sourceCodeLocationInfo: true });
  const patches = [];
  $('h1,h2,h3,h4,p,li,td,th,figcaption').each((_, el) => {
    const loc = el.sourceCodeLocation;
    if (!loc?.startTag || !loc.endTag || $(el).closest('aside.notes,pre,code,svg,.mermaid').length ||
      $(el).find('p,li,h1,h2,h3,h4,img,svg,canvas,video,audio,pre,code,input,button').length || $(el).text().includes('$')) return;
    const id = `text-${patches.length}`;
    patches.push({ id, start: loc.startTag.endOffset, end: loc.endTag.startOffset });
    $(el).attr('data-edit-id', id).attr('contenteditable', 'plaintext-only');
  });
  return { html: $.html(), patches };
}
async function createEditor(file, port = 0) {
  const target = path.resolve(file);
  if (!fs.lstatSync(target).isFile()) throw new Error('Choose a regular HTML file');
  const token = crypto.randomBytes(32).toString('hex');
  let origin;
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    if (req.method === 'POST' && pathname === '/save') {
      if (req.headers.origin !== origin || req.headers['x-edit-token'] !== token) { res.writeHead(403); res.end('Forbidden'); return; }
      let body = '', length = 0;
      req.on('data', chunk => { length += chunk.length; if (length <= 2 * 1024 * 1024) body += chunk; });
      req.on('end', () => {
        if (length > 2 * 1024 * 1024) { res.writeHead(413); res.end('Too large'); return; }
        try {
          const request = JSON.parse(body); const source = fs.readFileSync(target, 'utf8');
          if (request.baseHash !== digest(source)) { res.writeHead(409); res.end('Source changed; reload and reconcile edits'); return; }
          if (!Array.isArray(request.patches)) throw new Error('Patches required');
          const map = new Map(editable(source).patches.map(p => [p.id, p]));
          const seen = new Set();
          const changes = request.patches.map(p => {
            if (!p || !map.has(p.id) || seen.has(p.id) || typeof p.text !== 'string') throw new Error('Invalid text patch');
            seen.add(p.id); return { ...map.get(p.id), text: escape(p.text) };
          }).sort((a, b) => b.start - a.start);
          let output = source;
          for (const p of changes) output = output.slice(0, p.start) + p.text + output.slice(p.end);
          if (output !== source) write(target, output, true);
          res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ saved: true, baseHash: digest(output), backup_created: output !== source }));
        } catch { res.writeHead(400); res.end('Invalid save request'); }
      });
      return;
    }
    if (req.method === 'GET' && (pathname === '/' || pathname === `/${path.basename(target)}`)) {
      const source = fs.readFileSync(target, 'utf8'); const page = editable(source);
      const injection = `<div id="research-text-editor" style="position:fixed;right:8px;top:8px;z-index:100000;background:#fff;color:#111;padding:10px;font:16px sans-serif"><button id="save-source-text">保存文字</button><span id="edit-status"></span></div>
<script>(function(){const patches=new Map();document.querySelectorAll('[data-edit-id]').forEach(el=>el.addEventListener('input',()=>patches.set(el.dataset.editId,el.textContent)));
document.getElementById('save-source-text').onclick=async()=>{const r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json','X-Edit-Token':${JSON.stringify(token)}},body:JSON.stringify({baseHash:${JSON.stringify(digest(source))},patches:Array.from(patches,([id,text])=>({id,text}))})});if(r.ok)location.reload();else document.getElementById('edit-status').textContent=await r.text();};})();</script>`;
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
      res.end(page.html.replace('</body>', injection + '</body>')); return;
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); res.end(); return; }
    staticFile(req, res, path.dirname(target));
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  origin = `http://127.0.0.1:${server.address().port}`;
  return { server, origin };
}
if (require.main === module) {
  (async () => {
    if (!process.argv[2] || process.argv[2].startsWith('--')) throw new Error('Usage: node edit-html.js talk.html [--port 3456]');
    const o = args(process.argv.slice(3), ['port']);
    if (o.port && (!/^\d+$/.test(o.port) || Number(o.port) > 65535)) throw new Error('Invalid port');
    const app = await createEditor(process.argv[2], Number(o.port || 0));
    console.log(`Text editor: ${app.origin}/`); console.log('Edits save source text only, with backup and source-change checks. Ctrl+C to stop.');
  })().catch(e => { console.error(e.message); process.exitCode = 1; });
}
module.exports = { createEditor, editable };
