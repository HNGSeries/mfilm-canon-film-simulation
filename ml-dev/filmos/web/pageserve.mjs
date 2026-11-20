// The site as GitHub Pages serves it, and the browser that opens it: for the page tests
// (pagetest.mjs, installtest.mjs). Needs Playwright with a Chromium (npm i playwright && npx
// playwright install chromium). On a computer that has Chrome or Edge and only playwright-core:
// MFILM_BROWSER=msedge (or chrome), and PLAYWRIGHT=<path to playwright-core> if it isn't installed here.

import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.wasm': 'application/wasm', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.mp4': 'video/mp4',
  '.zip': 'application/zip',
};

// the site in ROOT on 127.0.0.1, on a free port
export function serve(ROOT) {
  ROOT = resolve(ROOT);
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = normalize(join(ROOT, path));
    if (file !== ROOT && !file.startsWith(ROOT + sep)) { res.writeHead(403).end(); return; }
    try {
      if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
      const body = await readFile(file);
      res.writeHead(200, { 'Content-Type': TYPES[extname(file)] || 'application/octet-stream' }).end(body);
    } catch {
      res.writeHead(404).end();
    }
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => ok(server)));
}

export async function browser() {
  const where = process.env.PLAYWRIGHT;
  const pw = await import(where ? pathToFileURL(resolve(where, 'index.mjs')).href : 'playwright');
  const channel = process.env.MFILM_BROWSER;
  return pw.chromium.launch(channel ? { channel } : {});
}
