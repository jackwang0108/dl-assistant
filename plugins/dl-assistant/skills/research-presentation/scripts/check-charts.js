#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const cheerio = require('cheerio');
const { chartConfig } = require('../assets/runtime');
const { contained } = require('./lib');
function validateChart(config, type) {
  const errors = [];
  if (!['line', 'bar', 'pie', 'doughnut', 'radar', 'polarArea', 'bubble', 'scatter'].includes(type)) errors.push('Unsupported chart type');
  if (!config || typeof config !== 'object' || !Array.isArray(config.data?.datasets) || !config.data.datasets.length) return [...errors, 'Nonempty data.datasets required'];
  for (const set of config.data.datasets) {
    if (!Array.isArray(set.data) || !set.data.length) { errors.push('Nonempty dataset values required'); continue; }
    for (const value of set.data) {
      if (value === null) continue;
      if (typeof value === 'number' && Number.isFinite(value)) continue;
      if (value && typeof value === 'object' && Number.isFinite(value.x) && Number.isFinite(value.y) && (type !== 'bubble' || Number.isFinite(value.r))) continue;
      errors.push('Chart values must be finite numbers, null or valid x/y points');
    }
    if (Array.isArray(config.data.labels) && !['scatter', 'bubble'].includes(type) && config.data.labels.length !== set.data.length) errors.push('Label and value lengths differ');
  }
  return errors;
}
function check(file) {
  const html = fs.readFileSync(file, 'utf8'); const $ = cheerio.load(html);
  const results = [];
  $('canvas[data-chart]').each((i, el) => {
    let errors = [];
    try {
      const source = $(el).attr('data-chart-src');
      if (source && (/^[a-z]+:/i.test(source) || source.startsWith('//'))) throw new Error('Chart data must be a local file');
      const text = source ? fs.readFileSync(contained(path.dirname(path.resolve(file)), source), 'utf8') : ($(el).html().match(/<!--([\s\S]*?)-->/)?.[1] || '');
      errors = validateChart(chartConfig(text), $(el).attr('data-chart'));
    } catch (e) { errors.push(e.message); }
    results.push({ chart: i + 1, id: $(el).attr('id') || null, errors });
  });
  return { charts: results.length, results, passed: results.every(r => !r.errors.length) };
}
if (require.main === module) {
  try { if (!process.argv[2]) throw new Error('Usage: node check-charts.js talk.html'); const r = check(process.argv[2]); console.log(JSON.stringify(r)); process.exitCode = r.passed ? 0 : 1; }
  catch (e) { console.error(e.message); process.exitCode = 1; }
}
module.exports = { check, validateChart };
