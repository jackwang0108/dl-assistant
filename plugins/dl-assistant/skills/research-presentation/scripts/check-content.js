#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const cheerio = require('cheerio');
const { args, contained, digest, write } = require('./lib');
function check(plan, html, root) {
  const errors = [], incomplete = [], warnings = [];
  const text = value => typeof value === 'string' && value.trim().length > 0;
  const $ = cheerio.load(html); const leaves = $('.slides section').filter((_, el) => $(el).children('section').length === 0);
  if (plan.schema_version !== 1 || !Array.isArray(plan.slides) || !plan.slides.length) return { errors: ['Plan needs schema_version=1 and slides'], incomplete, warnings, passed: false };
  for (const key of ['title', 'audience', 'goal', 'scenario']) if (!text(plan[key])) errors.push(`Missing plan.${key}`);
  if (!Number.isFinite(plan.talk_minutes) || plan.talk_minutes <= 0) errors.push('Positive talk_minutes required');
  const sourceIds = new Set();
  for (const source of plan.sources || []) {
    if (!text(source.id) || sourceIds.has(source.id) || !text(source.ref)) errors.push('Source needs unique id and actual reference');
    sourceIds.add(source.id);
  }
  const assets = new Map();
  for (const asset of plan.assets || []) {
    if (!text(asset.id) || assets.has(asset.id)) errors.push('Asset IDs must be unique');
    assets.set(asset.id, asset);
    if (!text(asset.purpose) || !text(asset.alt) || !asset.source || !text(asset.source.ref) || !text(asset.source.kind)) errors.push(`Asset ${asset.id}: purpose, alt and source required`);
    if (['generated', 'schematic', 'example'].includes(asset.source?.kind) && !text(asset.label)) errors.push(`Asset ${asset.id}: illustration/example label required`);
    if (asset.status !== 'ready') incomplete.push(`Asset ${asset.id}: not ready`);
    else {
      try {
        const file = contained(root, asset.file);
        if (!fs.statSync(file).isFile()) throw new Error('Not a file');
        if (asset.sha256 && asset.sha256 !== digest(fs.readFileSync(file))) errors.push(`Asset ${asset.id}: checksum differs`);
      } catch { errors.push(`Asset ${asset.id}: local file missing or outside deck`); }
    }
  }
  const ids = new Set(); let seconds = 0, visualPages = 0;
  for (const slide of plan.slides) {
    if (!text(slide.id) || ids.has(slide.id)) errors.push('Slide IDs must be unique');
    ids.add(slide.id);
    const page = leaves.filter((_, el) => $(el).attr('id') === slide.id);
    if (page.length !== 1) errors.push(`Slide ${slide.id}: missing or duplicate HTML section`);
    for (const key of ['title', 'question', 'message', 'notes']) if (!text(slide[key])) errors.push(`Slide ${slide.id}: ${key} required`);
    if (!Number.isFinite(slide.seconds) || slide.seconds <= 0) errors.push(`Slide ${slide.id}: positive seconds required`); else if (slide.role !== 'appendix') seconds += slide.seconds;
    if (!Array.isArray(slide.evidence_ids)) errors.push(`Slide ${slide.id}: evidence_ids must be an array`);
    for (const id of slide.evidence_ids || []) if (!sourceIds.has(id)) errors.push(`Slide ${slide.id}: unknown evidence ID`);
    const visual = slide.visual;
    if (!visual || !['image', 'diagram', 'plot', 'media', 'interaction', 'text'].includes(visual.kind) || !text(visual.purpose)) { errors.push(`Slide ${slide.id}: visual choice and purpose required`); continue; }
    if (visual.kind === 'text') { if (!text(visual.text_only_reason)) errors.push(`Slide ${slide.id}: text-only reason required`); }
    else {
      visualPages++;
      if (!Array.isArray(visual.asset_ids) || !visual.asset_ids.length) errors.push(`Slide ${slide.id}: visual asset IDs required`);
      for (const id of visual.asset_ids || []) {
        if (!assets.has(id)) errors.push(`Slide ${slide.id}: unknown asset ID`);
        const placed = page.find('[data-asset-id]').filter((_, el) => $(el).attr('data-asset-id') === id && !$(el).closest('aside.notes').length);
        const realVisual = placed.filter((_, el) => $(el).is('img,svg,canvas,audio,video,iframe,.mermaid') || $(el).find('img,svg,canvas,audio,video,iframe,.mermaid').length);
        if (!realVisual.length) incomplete.push(`Slide ${slide.id}: planned visual ${id} not placed as an image, diagram, chart or media`);
        placed.filter('img').each((_, el) => {
          if (assets.has(id) && assets.get(id).file && path.resolve(root, $(el).attr('src') || '') !== path.resolve(root, assets.get(id).file)) errors.push(`Slide ${slide.id}: displayed image differs from declared asset`);
        });
      }
    }
    if (['media', 'interaction'].includes(visual.kind) && !text(visual.fallback_id)) errors.push(`Slide ${slide.id}: static fallback required`);
    if (visual.fallback_id && !page.find('[id]').filter((_, el) => $(el).attr('id') === visual.fallback_id).length) errors.push(`Slide ${slide.id}: fallback element missing`);
    page.find('img').each((_, el) => { if (!text($(el).attr('alt'))) errors.push(`Slide ${slide.id}: image alt required`); });
    page.find('video,audio,iframe,[data-interactive]').each((_, el) => {
      const id = $(el).attr('data-static-fallback');
      if (!text(id) || !page.find('[id]').filter((_, e) => $(e).attr('id') === id).length) errors.push(`Slide ${slide.id}: media/widget fallback missing`);
    });
    if (page.find('[data-placeholder]').length) incomplete.push(`Slide ${slide.id}: unresolved content/visual placeholder`);
  }
  leaves.each((_, el) => { if (!ids.has($(el).attr('id'))) errors.push('HTML contains an unplanned slide or slide without ID'); });
  if (seconds > plan.talk_minutes * 60) errors.push('Planned speaking time exceeds talk_minutes; shorten main talk or move details to appendix');
  if (visualPages === 0) warnings.push('All pages are text-only: review whether concepts, samples or results need visual explanation');
  return { passed: errors.length === 0 && incomplete.length === 0, errors, incomplete, warnings, slides: plan.slides.length, visual_pages: visualPages, estimated_seconds: seconds,
    limitation: 'Checks declarations and local files; does not certify truth, image relevance, licenses, legibility or speaking time' };
}
if (require.main === module) {
  try {
    const o = args(process.argv.slice(2), ['plan', 'html', 'report'], ['force']);
    if (!o.plan || !o.html) throw new Error('Usage: node check-content.js --plan talk.plan.json --html talk.html [--report check.json]');
    const result = check(JSON.parse(fs.readFileSync(o.plan)), fs.readFileSync(o.html, 'utf8'), path.dirname(path.resolve(o.html)));
    if (o.report) write(o.report, JSON.stringify(result, null, 2), o.force);
    console.log(JSON.stringify(result)); process.exitCode = result.errors.length ? 1 : result.incomplete.length ? 3 : 0;
  } catch (e) { console.error(e.message); process.exitCode = 1; }
}
module.exports = { check };
