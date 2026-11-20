// The sections under the camera: the films (fos/films.json), the cameras
// (fos/cameras.json), both made by ml-dev/filmos/web/sitedata.py from FILMS.md and
// cameras.txt; and Darkrooms' download links, from the newest Darkrooms release.

import { T, currentLang as lang } from './i18n.js';
import { latestRelease, DARKROOMS } from './releases.js';

const REPO = 'https://github.com/HNGSeries/mfilm-canon-film-simulation';
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// ---------------------------------------------------------------- films
// One large frame and the shelf beside it: picking a film develops the frame again with it, as a print
// comes up in the developer. The frame opens larger in the lightbox, which steps through the shelf.

const tabs = document.getElementById('shelves');
const grid = document.getElementById('films-grid');
const view = document.getElementById('film-view');
const frame = view.querySelector('.view-frame');
const big = frame.querySelector('img');
const lb = document.getElementById('lightbox');
const still = matchMedia('(prefers-reduced-motion: reduce)');
let shelves = [], current = 0, shown = [], at = 0, seen = false;

function drawTabs() {
  tabs.innerHTML = shelves.map((s, i) =>
    `<button role="tab" aria-selected="${i === current}" class="${i === current ? 'on' : ''}" data-i="${i}">` +
    `${esc(T('shelf.' + s.shelf))}<span>${s.films.length}</span></button>`).join('');
}
// how many film stocks are measured against the real film, from each one's state (ml-dev/films/states.py)
function drawState() {
  const all = shelves.flatMap((s) => s.films);
  const names = (kind) => all.filter((f) => f.state === kind).map((f) => f.name);
  document.getElementById('films-state').innerHTML =
    T('films.state', all.length, names('measured'), names('style').length, names('impression').length, names('own'));
}
function drawShelf() {
  shown = shelves[current].films;
  grid.innerHTML = shown.map((f, i) => `
    <li><button class="film${i === at ? ' on' : ''}" data-i="${i}" aria-pressed="${i === at}">
      <img src="fos/films/${f.key}.jpg" alt="" loading="lazy" decoding="async">
      <b>${esc(f.name)}</b>
      <span>ISO ${esc(f.iso)} · ${esc(f.process)}</span>
    </button></li>`).join('');
}
function caption() {
  const f = shown[at];
  const c = view.querySelector('figcaption');
  c.querySelector('b').textContent = f.name;
  c.querySelector('.spec').textContent = `ISO ${f.iso} · ${f.process}`;
  c.querySelector('p').innerHTML = `${esc(f.desc)}<br><span class="state">${esc(lang() === 'th' ? f.state_th : f.state_en)}</span>`;
  frame.setAttribute('aria-label', T('films.open') + ': ' + f.name);
}
// full: from bare paper, the first time the frame is seen; otherwise the short, light re-develop
function develop(full) {
  big.classList.remove('developing', 'redeveloping');
  if (still.matches) return;
  void big.offsetWidth;
  big.classList.add(full ? 'developing' : 'redeveloping');
}
// show film i of the shelf in the large frame; once the frame has been seen, each change develops it again
function pick(i) {
  at = i;
  const f = shown[at];
  for (const b of grid.querySelectorAll('.film')) {
    const on = Number(b.dataset.i) === at;
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on);
  }
  caption();
  big.alt = f.name;
  big.onload = () => { if (seen) develop(false); };
  big.src = `fos/films/${f.key}.jpg`;
}
tabs.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  current = Number(b.dataset.i);
  at = 0;
  drawTabs(); drawShelf(); pick(0);
  grid.scrollTop = 0;
});
grid.addEventListener('click', (e) => { const b = e.target.closest('.film'); if (b) pick(Number(b.dataset.i)); });

// the first time the frame comes into view it develops as it rises into the page; the image is
// there all along, so nothing waits on this
if (!still.matches && 'IntersectionObserver' in window) {
  new IntersectionObserver((list, obs) => {
    if (!list.some((x) => x.isIntersecting)) return;
    seen = true; obs.disconnect(); develop(true);
  }, { threshold: 0.02 }).observe(frame);
} else {
  seen = true;
}

function openFilm(i) {
  at = (i + shown.length) % shown.length;
  const f = shown[at];
  lb.querySelector('img').src = `fos/films/${f.key}.jpg`;
  lb.querySelector('img').alt = f.name;
  lb.querySelector('figcaption').innerHTML = `<b>${esc(f.name)}</b> ISO ${esc(f.iso)} · ${esc(f.process)}<br><span>${esc(f.desc)}</span>` +
    `<br><span>${esc(lang() === 'th' ? f.state_th : f.state_en)}</span>`;
  lb.hidden = false;
  document.body.classList.add('noscroll');
}
function closeFilm() { lb.hidden = true; document.body.classList.remove('noscroll'); pick(at); }
frame.addEventListener('click', () => openFilm(at));
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
// a camera's note as cameras.txt writes it: `code`, *emphasis*, [text](TESTING.md#…) and #issue numbers
function linkIssues(s) {
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, t, u) => `<a href="${/^https?:/.test(u) ? u : REPO + '/blob/main/' + u}">${t}</a>`)
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/(?<![&\w/-])#(\d+)\b(?!;)/g, `<a href="${REPO}/issues/$1">#$1</a>`);   // not &#39;, not a link's #anchor
}
function drawCameras() {
  if (!cams) return;
  document.getElementById('cam-rows').innerHTML = cams.cameras.map((c) => `
    <tr>
      <td><b>${esc(c.name)}</b><span class="fw-m">${esc(c.firmware)}</span></td>
      <td>${esc(c.firmware)}</td>
      <td><span class="st ${c.status}"><i aria-hidden="true"></i>${esc(T('cs.' + c.status))}</span></td>
      <td class="note">${linkIssues((lang() === 'th' && c.note_th) || c.note)}</td>
    </tr>`).join('');
  const later = cams.later.map((c) => c.name.replace(/^Canon EOS /, '')).join(', ');
  document.getElementById('cam-later').innerHTML = `<b>${esc(T('cams.later'))}</b> ${esc(later)}`;
}

// ---------------------------------------------------------------- Darkrooms

async function darkrooms() {
  const r = await latestRelease((tag) => tag.startsWith('app-v'), DARKROOMS);
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
  drawTabs(); drawShelf(); pick(0); drawState(); drawCameras();
}).catch((e) => {
  console.warn('sections:', e);
  grid.innerHTML = `<li class="muted">${esc(T('films.none'))} <a class="link" href="${REPO}/blob/main/FILMS.md">FILMS.md →</a></li>`;
});
darkrooms().catch((e) => console.warn('darkrooms:', e));
document.addEventListener('mfilm:lang', () => {
  if (shelves.length) { drawTabs(); drawState(); caption(); }
  drawCameras();
  const v = document.getElementById('dr-version');
  if (v.dataset.version) v.textContent = T('dr.unsigned') + ' ' + T('dr.version', v.dataset.version);
});
