// The download: pick the camera, pay what you want (US$0 to 99), get its zip.
// $0 downloads straight away. More goes to Stripe Checkout for exactly that
// amount (the Darkrooms licence server's /v1/donate makes the page), and
// Stripe sends the visitor back here with ?thanks=1, where the download starts.

import { T } from './i18n.js';

// the cameras with a release zip, M-Film-camera-<platform>.zip (ml-dev/cameras.txt; keep the two together)
const CAMERAS = [
  ['EOSM.202', 'Canon EOS M', 'working'],
  ['6D.116', 'Canon EOS 6D', 'working'],
  ['60D.111', 'Canon EOS 60D', 'working'],
  ['50D.109', 'Canon EOS 50D', 'working'],
  ['500D.111', 'Canon EOS 500D / Rebel T1i / Kiss X3', 'working'],
  ['550D.109', 'Canon EOS 550D / Rebel T2i / Kiss X4', 'working'],
  ['600D.102', 'Canon EOS 600D / Rebel T3i / Kiss X5', 'working'],
  ['100D.101', 'Canon EOS 100D / Rebel SL1 / Kiss X7', 'working'],
  ['650D.104', 'Canon EOS 650D / Rebel T4i / Kiss X6i', 'working'],
  ['700D.115', 'Canon EOS 700D / Rebel T5i / Kiss X7i', 'issues'],
  ['70D.112', 'Canon EOS 70D', 'issues'],
  ['5D3.113', 'Canon EOS 5D Mark III (firmware 1.1.3)', 'issues'],
  ['5D3.123', 'Canon EOS 5D Mark III (firmware 1.2.3)', 'issues'],
  ['5D2.212', 'Canon EOS 5D Mark II', 'issues'],
  ['1100D.105', 'Canon EOS 1100D / Rebel T3 / Kiss X50', 'testing'],
];
const REPO = 'https://github.com/HNGSeries/mfilm-canon-film-simulation';
const DONATE = 'https://darkrooms-licence.suphalapruksasathit.workers.dev/v1/donate';
const zipUrl = (p) => `${REPO}/releases/latest/download/M-Film-camera-${p}.zip`;

const dlg = document.getElementById('dl');
const sel = document.getElementById('dl-camera');
const note = document.getElementById('dl-camera-note');
const amount = document.getElementById('dl-amount');
const range = document.getElementById('dl-range');
const go = document.getElementById('dl-go');
const err = document.getElementById('dl-err');
const presets = [...dlg.querySelectorAll('.presets button')];

function fillCameras() {
  const keep = sel.value || remembered() || 'EOSM.202';
  sel.innerHTML = '';
  for (const [p, name, status] of CAMERAS) {
    const o = document.createElement('option');
    o.value = p;
    o.textContent = status === 'working' ? name : `${name} · ${T('dl.' + status)}`;
    sel.append(o);
  }
  sel.value = keep;
  showNote();
}
function showNote() {
  const c = CAMERAS.find(([p]) => p === sel.value);
  note.textContent = c && c[2] !== 'working' ? T('dl.note.' + c[2]) : '';
  try { localStorage.setItem('mfilm.camera', sel.value); } catch {}
}
function remembered() { try { return localStorage.getItem('mfilm.camera'); } catch { return null; } }

function setAmount(v, from) {
  v = Math.max(0, Math.min(99, Math.round(Number(v) || 0)));
  if (from !== amount) amount.value = String(v);
  range.value = String(v);
  presets.forEach((b) => b.classList.toggle('on', Number(b.dataset.amount) === v));
  go.textContent = v ? T('dl.pay', v) : T('dl.freeGo');
  err.textContent = '';
  return v;
}

function startDownload(p) {
  const a = document.createElement('a');
  a.href = zipUrl(p);
  a.rel = 'noopener';
  document.body.append(a);
  a.click();
  a.remove();
}

function thanks(p) {
  dlg.querySelector('.dl-ask').hidden = true;
  dlg.querySelector('.dl-thanks').hidden = false;
  const again = document.getElementById('dl-again');
  again.href = zipUrl(p);
  open();
  startDownload(p);
}

function open() {
  if (!dlg.open) dlg.showModal();
}

async function submit() {
  const p = sel.value;
  const v = setAmount(amount.value);
  if (!v) return thanks(p);
  go.disabled = true;
  go.textContent = T('dl.wait');
  try {
    const r = await fetch(DONATE, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      // the page Stripe sends them back to: this one, wherever the site is (github.io now, a domain later)
      body: new URLSearchParams({ amount: String(v), camera: p, back: location.origin + location.pathname.replace(/index\.html$/, '') }),
    });
    const o = await r.json().catch(() => ({}));
    if (!r.ok || !o.url) throw new Error(o.error || 'Stripe');
    location.href = o.url;
  } catch (e) {
    console.warn('donate:', e);
    err.innerHTML = T('dl.err', zipUrl(p));
    go.disabled = false;
    setAmount(v);
  }
}

// ---------------------------------------------------------------- wiring

fillCameras();
setAmount(5);
sel.addEventListener('change', showNote);
amount.addEventListener('input', () => setAmount(amount.value, amount));
amount.addEventListener('blur', () => setAmount(amount.value));
range.addEventListener('input', () => setAmount(range.value, range));
presets.forEach((b) => b.addEventListener('click', () => setAmount(b.dataset.amount)));
go.addEventListener('click', submit);
dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });   // outside the box
dlg.addEventListener('close', () => {
  dlg.querySelector('.dl-ask').hidden = false;
  dlg.querySelector('.dl-thanks').hidden = true;
});
for (const a of document.querySelectorAll('[data-download]')) {
  a.addEventListener('click', (e) => { e.preventDefault(); open(); });
}
document.addEventListener('mfilm:lang', () => { fillCameras(); setAmount(amount.value); });

// back from Stripe
const q = new URLSearchParams(location.search);
if (q.get('thanks') === '1') {
  const p = CAMERAS.some(([c]) => c === q.get('camera')) ? q.get('camera') : sel.value;
  sel.value = p;
  history.replaceState(null, '', location.pathname + '#download');
  thanks(p);
}
