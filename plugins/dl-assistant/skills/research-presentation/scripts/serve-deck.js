#!/usr/bin/env node
'use strict';
const path = require('node:path');
const { serve } = require('./lib');
(async () => {
  if (!process.argv[2]) throw new Error('Usage: node serve-deck.js talk.html');
  const html = path.resolve(process.argv[2]);
  const app = await serve(path.dirname(html));
  console.log(`${app.origin}/${encodeURIComponent(path.basename(html))}`);
  console.log('Local preview only. Ctrl+C to stop.');
})().catch(e => { console.error(e.message); process.exitCode = 1; });
