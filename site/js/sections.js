// The sections under the camera: the films (fos/films.json), the cameras
// (fos/cameras.json), both made by ml-dev/filmos/web/sitedata.py from FILMS.md and
// cameras.txt; and Darkrooms' download links, from the newest Darkrooms release.

import { T, currentLang as lang } from './i18n.js';
import { latestRelease } from './releases.js';

const REPO = 'https://github.com/HNGSeries/mfilm-canon-film-simulation';
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// ---------------------------------------------------------------- films

const tabs = document.getElementById('shelves');
const grid = document.getElementById('films-grid');
const lb = document.getElementById('lightbox');
let shelves = [], current = 0, shown = [], at = 0;

function drawTabs() {
  tabs.innerHTML = shelves.map((s, i) =>
    `<button role="tab" aria-selected="${i === current}" class="${i === current ? 'on' : ''}" data-i="${i}">` +
    `${esc(T('shelf.' + s.shelf))}<span>${s.films.length}</span></button>`).join('');
}
function drawShelf() {
  shown = shelves[current].films;
  grid.innerHTML = shown.map((f, i) => `
    <button class="film" data-i="${i}">
      <img src="fos/films/${f.key}.jpg" alt="${esc(f.name)}" loading="lazy" decoding="async">
      <b>${esc(f.name)}</b>
      <span>ISO ${esc(f.iso)} · ${esc(f.process)}</span>
    </button>`).join('');
}
tabs.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  current = Number(b.dataset.i);
  drawTabs(); drawShelf();
});

function openFilm(i) {
  at = (i + shown.length) % shown.length;
  const f = shown[at];
  lb.querySelector('img').src = `fos/films/${f.key}.jpg`;
  lb.querySelector('img').alt = f.name;
  lb.querySelector('figcaption').innerHTML = `<b>${esc(f.name)}</b> ISO ${esc(f.iso)} · ${esc(f.process)}<br><span>${esc(f.desc)}</span>`;
  lb.hidden = false;
  document.body.classList.add('noscroll');
}
function closeFilm() { lb.hidden = true; document.body.classList.remove('noscroll'); }
grid.addEventListener('click', (e) => { const b = e.target.closest('.film'); if (b) openFilm(Number(b.dataset.i)); });
lb.querySelector('.lb-x').addEventListener('click', closeFilm);
lb.querySelector('.prev').addEventListener('click', () => openFilm(at - 1));
lb.querySelector('.next').addEventListener('click', () => openFilm(at + 1));
lb.addEventListener('click', (e) => { if (e.target === lb) closeFilm(); });
addEventListener('keydown', (e) => {
  if (lb.hidden) return;
  if (e.key === 'Escape') closeFilm();
  if (e.key === 'ArrowLeft') openFilm(at - 1);
  if (e.key === 'ArrowRight') openFilm(at + 1);
  e.stopImmediatePropagation();
}, true);

// ---------------------------------------------------------------- cameras

let cams = null;
const STATUS = { working: '✓', issues: '!', testing: '?', nodark: '✓' };
function linkIssues(s) {
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/(?<![&\w])#(\d+)\b(?!;)/g, `<a href="${REPO}/issues/$1">#$1</a>`);   // not &#39;
}
function drawCameras() {
  if (!cams) return;
  document.getElementById('cam-rows').innerHTML = cams.cameras.map((c) => `
    <tr>
      <td><b>${esc(c.name)}</b></td>
      <td>${esc(c.firmware)}</td>
      <td><span class="st ${c.status}"><i>${STATUS[c.status] || ''}</i>${esc(T('cs.' + c.status))}</span></td>
      <td class="note">${linkIssues((lang() === 'th' && c.note_th) || c.note)}</td>
    </tr>`).join('');
  const later = cams.later.map((c) => c.name.replace(/^Canon EOS /, '')).join(', ');
  document.getElementById('cam-later').innerHTML = `<b>${esc(T('cams.later'))}</b> ${esc(later)}`;
}

// ---------------------------------------------------------------- Darkrooms

async function darkrooms() {
  const r = await latestRelease((tag) => tag.startsWith('app-v'));
  if (!r) return;
  for (const a of document.querySelectorAll('#dr-links [data-os]')) {
    const asset = r.assets.find((x) => x.name.includes(a.dataset.os) && x.name.endsWith('.zip'));
    if (asset) a.href = asset.browser_download_url;
  }
  const v = document.getElementById('dr-version');
  v.dataset.version = r.tag.replace(/^app-v/, '');
  v.textContent = T('dr.unsigned') + ' ' + T('dr.version', v.dataset.version);
}

// ---------------------------------------------------------------- go

Promise.all([
  fetch('fos/films.json').then((r) => r.json()),
  fetch('fos/cameras.json').then((r) => r.json()),
]).then(([f, c]) => {
  shelves = f; cams = c;
  drawTabs(); drawShelf(); drawCameras();
}).catch((e) => {
  console.warn('sections:', e);
  grid.innerHTML = `<p class="muted">${esc(T('films.none'))} <a class="link" href="${REPO}/blob/main/FILMS.md">FILMS.md →</a></p>`;
});
darkrooms().catch((e) => console.warn('darkrooms:', e));
document.addEventListener('mfilm:lang', () => {
  if (shelves.length) drawTabs();
  drawCameras();
  const v = document.getElementById('dr-version');
  if (v.dataset.version) v.textContent = T('dr.unsigned') + ' ' + T('dr.version', v.dataset.version);
});
