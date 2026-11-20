// Does mfilm.app shoot and develop a roll? (#143)
//
// The page as a visitor uses it, in a headless browser: load a roll, shoot it,
// develop it, and fail unless every frame comes out of the darkroom. #124 once
// left the page's card without colour tables, and from then on the page could
// not develop a single frame while every check passed (#103, fixed in #142).
//
//   node ml-dev/filmos/web/pagetest.mjs [site dir]      default: site
//
// Run after ml-dev/filmos/web/build.sh. Needs Playwright with a Chromium
// (npm i playwright && npx playwright install chromium). On a computer that
// has Chrome or Edge and only playwright-core: MFILM_BROWSER=msedge (or
// chrome), and PLAYWRIGHT=<path to playwright-core> if it isn't installed here.
//
// Portra 400 is always developed: it is the shelf's first film, and its table
// is mixed from its look. When the Film-Luts tables were made (TABLES.txt says
// "lut" for Portra 160), a roll of Portra 160 is developed too, so a table
// made from a LUT that isn't on the page is caught as well.

import { readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { serve, browser } from './pageserve.mjs';

const ROOT = resolve(process.argv[2] || 'site');
const SET = 7, RIGHT = 2;          // js/camera.js: KEY

// One roll of a film on a fresh page: load, shoot, develop. Returns what went wrong, or nothing.
async function roll(context, url, film) {
  const page = await context.newPage();
  const lines = [], problems = [];
  page.on('console', (m) => { const t = m.text(); if (t.startsWith('[fos]')) lines.push(t.slice(6)); });
  page.on('pageerror', (e) => problems.push(`page error: ${e.message}`));
  try {
    await page.goto(url);
    await page.waitForSelector('.loading.gone', { state: 'attached', timeout: 60000 });
    const steps = await page.evaluate(async ({ film, SET, RIGHT }) => {
      const m = window.mfilm;
      m.debug = true;
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const until = async (what, ok, ms) => {
        const t0 = performance.now();
        while (!ok()) {
          if (performance.now() - t0 > ms) throw new Error(`${what}: not within ${ms / 1000} s`);
          await sleep(100);
        }
      };
      const tap = async (k) => { m.press(k); await sleep(80); m.release(k); await sleep(400); };
      const seen = new Set();
      for (const e of ['loaded', 'finished', 'crash']) m.addEventListener(e, () => seen.add(e));
      // the darkroom at work and done (a roll whose frames all fail can be both within a poll)
      m.addEventListener('developing', (e) => seen.add(e.detail.a ? 'developing' : 'developed'));

      // the page starts with the boot animation (1.7 s, fos_ui.c), which a key only cuts short,
      // and fades to the shelf; then along the first shelf to the film
      const shelves = await fetch('fos/films.json').then((r) => r.json());
      const at = shelves[0].films.findIndex((f) => f.key === film);
      if (at < 0) throw new Error(`${film} is not on the first shelf`);
      await sleep(4000);
      for (let i = 0; i < at; i++) await tap(RIGHT);
      await tap(SET);
      await until('the roll loading', () => seen.has('loaded') && !m.ui && m.roll, 30000);
      if (m.roll.film !== film) throw new Error(`loaded ${m.roll.film}, not ${film}`);
      const frames = m.roll.exposures;

      // shoot it
      for (let shots = 0; !seen.has('finished');) {
        const r = await m.fire();
        if (r === 'shot') shots++;
        else await sleep(300);
        if (shots > frames || seen.has('crash')) throw new Error(`shooting: ${shots} shots and no end of the roll`);
        await sleep(100);
      }

      // develop it: a moment after the last frame the camera asks (web.c: end_due), and
      // SET is "Develop now". A second SET once, should the first have come too early.
      await until('the camera asking to develop', () => m.ui, 15000);
      await sleep(1500);
      await tap(SET);
      try {
        await until('developing to start', () => seen.has('developing'), 10000);
      } catch {
        await tap(SET);
        await until('developing to start', () => seen.has('developing'), 30000);
      }
      await until('developing to end', () => seen.has('developed') && !m.busy, 300000);
      if (seen.has('crash')) throw new Error('the film OS crashed');
      return { frames };
    }, { film, SET, RIGHT });
    await page.waitForTimeout(500);         // the last console lines on their way

    const developed = lines.filter((l) => /^darkroom: roll \d+ frame \d+ developed in /.test(l)).length;
    const missing = lines.filter((l) => /no colour table/.test(l));
    if (developed !== steps.frames) problems.push(`${developed} of ${steps.frames} frames developed`);
    if (missing.length) problems.push(`no colour table (${missing.length} lines), as: ${missing[0]}`);
    console.log(`${film}: ${developed} of ${steps.frames} frames developed${missing.length ? `, ${missing.length} without a colour table` : ''}`);
  } catch (e) {
    problems.push(e.message);
  } finally {
    if (problems.length) console.log(lines.slice(-12).map((l) => `    ${l}`).join('\n'));
    await page.close();
  }
  return problems.map((p) => `${film}: ${p}`);
}

const tables = await readFile(join(ROOT, 'fos', 'tables', 'TABLES.txt'), 'utf8').catch(() => '');
const films = ['portra400'];
if (/^LOOK\d+\.LUT\s+portra160\s+lut\b/m.test(tables)) films.push('portra160');
else console.log('portra160: not tried, the page has no Film-Luts tables (built with MFILM_PLAIN=1?)');

const server = await serve(ROOT);
const url = `http://127.0.0.1:${server.address().port}/`;
const b = await browser();
let problems = [];
try {
  const context = await b.newContext({ viewport: { width: 1280, height: 900 } });
  for (const film of films) problems = problems.concat(await roll(context, url, film));
} finally {
  await b.close();
  server.close();
}
if (problems.length) {
  console.log(`pagetest: FAILED\n${problems.map((p) => `  ${p}`).join('\n')}`);
  process.exit(1);
}
console.log('pagetest: all passed');
