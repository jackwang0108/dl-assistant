'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

function args(argv, values, flags = []) {
  const result = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, '');
    if (!argv[i].startsWith('--')) throw new Error(`Unexpected argument: ${argv[i]}`);
    if (flags.includes(key)) result[key] = true;
    else if (values.includes(key)) {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing --${key} value`);
      result[key] = argv[++i];
    } else throw new Error(`Unknown option: --${key}`);
  }
  return result;
}
function integer(value, label, min = 1, max = 500) {
  if (!/^\d+$/.test(String(value)) || Number(value) < min || Number(value) > max) {
    throw new Error(`${label} must be an integer from ${min} to ${max}`);
  }
  return Number(value);
}
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
function write(file, content, force = false) {
  const dest = path.resolve(file);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  if (fs.existsSync(dest)) {
    if (!force) throw new Error(`Output exists: ${dest}; use a new path or --force (creates backup)`);
    if (!fs.lstatSync(dest).isFile()) throw new Error('Output must be a regular file');
    fs.copyFileSync(dest, `${dest}.bak-${crypto.randomUUID()}`, fs.constants.COPYFILE_EXCL);
  }
  const temp = `${dest}.tmp-${crypto.randomUUID()}`;
  try {
    fs.writeFileSync(temp, content, { flag: 'wx' });
    fs.renameSync(temp, dest);
  } finally { if (fs.existsSync(temp)) fs.unlinkSync(temp); }
}
function contained(root, requested) {
  const base = fs.realpathSync(root);
  const target = fs.realpathSync(path.resolve(base, requested));
  const rel = path.relative(base, target);
  if (rel.startsWith(`..${path.sep}`) || rel === '..' || path.isAbsolute(rel)) throw new Error('Path outside presentation');
  return target;
}
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav', '.mp4': 'video/mp4', '.webm': 'video/webm', '.pdf': 'application/pdf' };
function staticFile(req, res, root) {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = contained(root, `.${pathname}`);
    const stat = fs.statSync(file);
    if (!stat.isFile()) throw new Error('Not a file');
    const headers = { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store', 'Accept-Ranges': 'bytes' };
    let start = 0, end = stat.size - 1, status = 200;
    if (req.headers.range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
      if (!match || (!match[1] && !match[2])) { res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` }); res.end(); return; }
      start = match[1] ? Number(match[1]) : Math.max(0, stat.size - Number(match[2]));
      end = match[1] && match[2] ? Math.min(Number(match[2]), stat.size - 1) : stat.size - 1;
      if (start > end || start >= stat.size) { res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` }); res.end(); return; }
      status = 206; headers['Content-Range'] = `bytes ${start}-${end}/${stat.size}`;
    }
    headers['Content-Length'] = stat.size ? end - start + 1 : 0;
    res.writeHead(status, headers);
    if (req.method === 'HEAD' || !stat.size) res.end(); else fs.createReadStream(file, { start, end }).pipe(res);
  } catch { res.writeHead(404); res.end('Not found'); }
}
async function serve(root) {
  const server = http.createServer((req, res) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); res.end(); return; }
    staticFile(req, res, root);
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return { server, origin: `http://127.0.0.1:${server.address().port}` };
}
module.exports = { args, integer, escape, digest, write, contained, staticFile, serve };
