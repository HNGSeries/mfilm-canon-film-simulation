// install.html, step 5: "Install onto the card from this page". In Chrome, Edge and Opera on a computer the
// page downloads the camera's zip from mfilm.app (dl/, published by pages.yml: GitHub's own downloads
// can't be fetched by a page), checks its SHA-256, unzips it and writes it onto the card the visitor
// picks (the File System Access API). Everywhere else the box stays hidden and the steps by hand are
// the way. What was tried before this was written, and why it is done this way: docs/easy-install.md.

import { T, addStrings } from './i18n.js';

// fflate, pinned; loaded only when the visitor installs
const FFLATE = 'https://cdn.jsdelivr.net/npm/fflate@0.8.2/esm/browser.js';
// in the 1300D's zip: for the computer, not the card (mlinstall writes the card's boot sectors)
const NOT_FOR_CARD = 'mlinstall-for-your-computer/';
// what a computer or a camera puts on a card by itself: these don't make a card "not empty"
const SYSTEM = /^(\.|System Volume Information$|\$RECYCLE\.BIN$|MISC$|EOSMISC$)/i;
const AT_ONCE = 4;      // files written at a time: Chrome checks each one after it is written

addStrings({
  en: {
    'ig.3.easy': 'You can skip this step in this browser: step 5 downloads M-Film and puts it on the card.',
    'ig.e.t': 'Install onto the card from this page',
    'ig.e.d': 'This browser can download M-Film and copy it onto the card for you. Put the card in the computer, choose it, and press Install.',
    'ig.e.pick': 'Choose the card…', 'ig.e.go': 'Install onto the card',
    'ig.e.or': 'Or copy the files by hand:',
    'ig.e.picked': (n) => `Card: ${n}. Press Install.`,
    'ig.e.dcim': 'You chose the DCIM folder. Choose the card itself: EOS_DIGITAL (or a similar name) on a Mac, a drive such as E: on Windows.',
    'ig.e.notcard': (n) => `"${n}" has files on it but no DCIM folder, so it isn't a camera's card. Choose the card itself: EOS_DIGITAL (or a similar name) on a Mac, a drive such as E: on Windows.`,
    'ig.e.old': (n) => `Card: ${n}. Magic Lantern is already on it. Format the card in the camera (step 4) and choose it again, or install over it.`,
    'ig.e.denied': 'The browser wasn\'t allowed to change the card. Choose it again and allow editing.',
    'ig.e.get': (v) => `Downloading M-Film ${v}…`,
    'ig.e.bad': 'The download was damaged. Try again. If it fails again, download the zip by hand (step 3).',
    'ig.e.fail': 'The download failed. Check the internet connection and try again, or download the zip by hand (step 3).',
    'ig.e.write': (n, of) => `Writing onto the card: ${n} of ${of} files…`,
    'ig.e.werr': (f, m) => `Couldn't write ${f} to the card (${m}). The card may be full or locked. Format it in the camera and try again, or copy the files by hand.`,
    'ig.e.done': (v, n) => `M-Film ${v} is on the card (${n} files). Eject the card (Windows: the USB icon → Eject; Mac: drag it to the bin), put it in the camera and go to step 6.`,
  },
  th: {
    'ig.3.easy': 'เบราว์เซอร์นี้ข้ามขั้นนี้ได้ ขั้นที่ 5 จะดาวน์โหลด M-Film แล้วติดตั้งลงการ์ดให้',
    'ig.e.t': 'ติดตั้งลงการ์ดจากหน้านี้',
    'ig.e.d': 'เบราว์เซอร์นี้ดาวน์โหลด M-Film แล้วก๊อปลงการ์ดให้ได้ เสียบการ์ดเข้าคอม กดเลือกการ์ด แล้วกดติดตั้ง',
    'ig.e.pick': 'เลือกการ์ด…', 'ig.e.go': 'ติดตั้งลงการ์ด',
    'ig.e.or': 'หรือก๊อปไฟล์เอง:',
    'ig.e.picked': (n) => `การ์ด: ${n} กดติดตั้งได้เลย`,
    'ig.e.dcim': 'ที่เลือกคือโฟลเดอร์ DCIM ให้เลือกตัวการ์ดแทน บน Mac ชื่อ EOS_DIGITAL หรือชื่อคล้ายกัน บน Windows เป็นไดรฟ์ เช่น E:',
    'ig.e.notcard': (n) => `"${n}" มีไฟล์อยู่แต่ไม่มีโฟลเดอร์ DCIM เลยไม่น่าใช่การ์ดของกล้อง ให้เลือกตัวการ์ด บน Mac ชื่อ EOS_DIGITAL หรือชื่อคล้ายกัน บน Windows เป็นไดรฟ์ เช่น E:`,
    'ig.e.old': (n) => `การ์ด: ${n} มี Magic Lantern อยู่แล้ว ฟอร์แมตการ์ดในกล้องก่อน (ขั้นที่ 4) แล้วเลือกการ์ดอีกครั้ง หรือจะติดตั้งทับก็ได้`,
    'ig.e.denied': 'เบราว์เซอร์ไม่ได้รับอนุญาตให้แก้ไขการ์ด เลือกการ์ดอีกครั้งแล้วกดอนุญาต',
    'ig.e.get': (v) => `กำลังดาวน์โหลด M-Film ${v}…`,
    'ig.e.bad': 'ไฟล์ที่ดาวน์โหลดมาเสีย ลองใหม่ ถ้ายังเสียอีกให้ดาวน์โหลดเอง (ขั้นที่ 3)',
    'ig.e.fail': 'ดาวน์โหลดไม่สำเร็จ เช็กอินเทอร์เน็ตแล้วลองใหม่ หรือดาวน์โหลดเอง (ขั้นที่ 3)',
    'ig.e.write': (n, of) => `กำลังเขียนลงการ์ด: ${n} จาก ${of} ไฟล์…`,
    'ig.e.werr': (f, m) => `เขียน ${f} ลงการ์ดไม่ได้ (${m}) การ์ดอาจเต็มหรือถูกล็อก ฟอร์แมตในกล้องแล้วลองใหม่ หรือก๊อปไฟล์เอง`,
    'ig.e.done': (v, n) => `M-Film ${v} อยู่บนการ์ดแล้ว (${n} ไฟล์) กด Eject การ์ด (Windows: ไอคอน USB → Eject, Mac: ลากไปถังขยะ) ใส่การ์ดในกล้อง แล้วไปขั้นที่ 6`,
  },
});

const $ = (id) => document.getElementById(id);
const box = $('ig-easy'), pick = $('ig-e-pick'), go = $('ig-e-go');
const bar = $('ig-e-bar'), msg = $('ig-e-msg');

let list = null;        // dl/index.json: { tag, zips: { platform: { name, size, sha256 } } }
let camera = null;      // { platform, firmware } from fos/cameras.json
let card = null;        // the picked card (FileSystemDirectoryHandle)
let busy = false;
let said = null;        // the last message, so it can be said again in the other language

const supported = 'showDirectoryPicker' in window && window.isSecureContext;
const listed = supported
  ? fetch('dl/index.json').then((r) => (r.ok ? r.json() : null)).catch(() => null).then((j) => { list = j; })
  : Promise.resolve();

const ICON = { ok: 'check', bad: 'alert', warn: 'alert' };
function say(key, cls, ...args) {
  said = key && [key, cls, args];
  msg.className = 'ig-e-msg' + (cls ? ' ' + cls : '');
  msg.textContent = '';
  if (!key) return;
  if (ICON[cls]) msg.insertAdjacentHTML('beforeend', `<svg class="i" aria-hidden="true"><use href="#i-${ICON[cls]}"/></svg>`);
  const t = document.createElement('span');
  t.textContent = T(key, ...args);
  msg.append(t);
}

// the line under the buttons: sweeping while it waits, then how much of the card is written
function meter(n, of) {
  bar.hidden = false;
  bar.classList.toggle('wait', of == null);
  bar.firstElementChild.style.width = of == null ? '' : (100 * n / of).toFixed(1) + '%';
}

function zip() { return camera && list && list.zips[camera.platform]; }
const version = () => list.tag.replace(/^v/, '');

function update() {
  pick.disabled = busy;
  go.disabled = busy || !card;
}

// the camera picked at the top of the page changed, or the language did
export async function easyCamera(c) {
  await listed;
  if (camera && c && camera.platform !== c.platform) { card = null; say(null); }
  camera = c;
  const show = !!zip();
  box.hidden = !show;
  $('ig-e-or').hidden = !show;
  $('ig-easy-skip').hidden = !show;
  if (!show) return;
  if (said) say(said[0], said[1], ...said[2]);
  update();
}

async function names(dir) {
  const out = [];
  for await (const [n, h] of dir.entries()) out.push({ n, dir: h.kind === 'directory' });
  return out;
}

pick.addEventListener('click', async () => {
  let d;
  say(null);
  try {
    d = await window.showDirectoryPicker({ id: 'mfilm-card', mode: 'readwrite' });
  } catch (e) {
    if (e.name !== 'AbortError') say('ig.e.denied', 'bad');
    return;
  }
  card = null;
  const all = await names(d);
  const seen = all.filter((x) => !SYSTEM.test(x.n));
  const has = (n, dir) => all.some((x) => x.n.toLowerCase() === n.toLowerCase() && x.dir === dir);
  if (d.name.toUpperCase() === 'DCIM' || seen.some((x) => x.dir && /^\d{3}[A-Z_]{5}$/i.test(x.n))) {
    say('ig.e.dcim', 'bad');
  } else if (!has('DCIM', true) && seen.length) {
    say('ig.e.notcard', 'bad', d.name);
  } else {
    card = d;
    if (has('ML', true) || has('autoexec.bin', false)) say('ig.e.old', 'warn', d.name);
    else say('ig.e.picked', 'ok', d.name);
  }
  update();
});

async function sha256(buf) {
  const h = new Uint8Array(await crypto.subtle.digest('SHA-256', buf));
  return Array.from(h, (b) => b.toString(16).padStart(2, '0')).join('');
}

// every "._" file under the folders and beside the files the zip put there: on a Mac, the browser
// marks what it writes as downloaded, and on a FAT32 or exFAT card that mark is a "._" file, which
// can stop the camera's installer (the guide's dot_clean). Nothing else on the card is touched.
async function cleanDots(dir, mine) {
  for (const { n, dir: isDir } of await names(dir)) {
    if (n.startsWith('._') && (!mine || mine.has(n.slice(2)))) {
      await dir.removeEntry(n).catch(() => {});
    } else if (isDir && (!mine || mine.has(n))) {
      await cleanDots(await dir.getDirectoryHandle(n), null);
    }
  }
}

go.addEventListener('click', async () => {
  const z = zip();
  if (!z || !card || busy) return;
  busy = true; update();
  meter();
  try {
    if ((await card.requestPermission({ mode: 'readwrite' })) !== 'granted') { say('ig.e.denied', 'bad'); return; }
    say('ig.e.get', null, version());
    let buf;
    try {
      const r = await fetch('dl/' + encodeURIComponent(z.name));
      if (!r.ok) throw new Error('HTTP ' + r.status);
      buf = new Uint8Array(await r.arrayBuffer());
    } catch (e) { console.warn('easy install:', e); say('ig.e.fail', 'bad'); return; }
    if ((await sha256(buf)) !== z.sha256) { say('ig.e.bad', 'bad'); return; }

    const { unzipSync } = await import(FFLATE);
    const files = unzipSync(buf);
    const paths = Object.keys(files)
      .filter((p) => !p.startsWith(NOT_FOR_CARD) && !p.startsWith('/') && !p.split('/').some((s) => s === '..' || s === '.'))
      .sort();
    // folders first, the zip's empty ones too (ML/doc), then the files, a few at a time
    const dirs = new Map([['', card]]);
    async function folder(path) {
      if (dirs.has(path)) return dirs.get(path);
      const i = path.lastIndexOf('/');
      const h = await (await folder(path.slice(0, Math.max(i, 0)))).getDirectoryHandle(path.slice(i + 1), { create: true });
      dirs.set(path, h);
      return h;
    }
    const todo = [];
    for (const p of paths) {
      if (p.endsWith('/')) { await folder(p.slice(0, -1)); continue; }
      const i = p.lastIndexOf('/');
      await folder(i < 0 ? '' : p.slice(0, i));
      todo.push(p);
    }
    let done = 0;
    meter(0, todo.length);
    say('ig.e.write', null, 0, todo.length);
    let next = 0, failed = null;
    async function worker() {
      while (next < todo.length && !failed) {
        const p = todo[next++], i = p.lastIndexOf('/');
        try {
          const fh = await dirs.get(i < 0 ? '' : p.slice(0, i)).getFileHandle(p.slice(i + 1), { create: true });
          const w = await fh.createWritable();
          await w.write(files[p]);
          await w.close();
        } catch (e) { failed = failed || [p, e]; return; }
        meter(++done, todo.length);
        say('ig.e.write', null, done, todo.length);
      }
    }
    await Promise.all(Array.from({ length: AT_ONCE }, worker));
    if (failed) {
      console.warn('easy install:', failed[0], failed[1]);
      say('ig.e.werr', 'bad', failed[0], failed[1].message || failed[1].name);
      return;
    }
    await cleanDots(card, new Set(paths.map((p) => p.split('/')[0])));
    say('ig.e.done', 'ok', version(), todo.length);
  } catch (e) {
    console.warn('easy install:', e);
    say('ig.e.werr', 'bad', 'M-Film', e.message || e.name);
  } finally {
    busy = false; bar.hidden = true; update();
  }
});
