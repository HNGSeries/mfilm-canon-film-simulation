import { Camera, KEY, OPEN } from './camera.js';
import { LiveView } from './liveview.js';
import { T, applyLang, toggleLang } from './i18n.js';
import { BODIES, bodyFor, buildCamera } from './bodies.js';

const cam = document.getElementById('cam');

// which camera: ?camera=6d (the picker sets it), the EOS M otherwise
const body = bodyFor(new URLSearchParams(location.search).get('camera') || 'eosm');
buildCamera(cam, body);
const picker = document.getElementById('model');
picker.innerHTML = BODIES.map((b) => `<option value="${b.id}">${b.name}${b.short.includes('/') ? ' / ' + b.short.split(' / ')[1] : ''}</option>`).join('');
picker.value = body.id;
picker.addEventListener('change', () => {
  const q = new URLSearchParams(location.search);
  q.set('camera', picker.value);
  try { localStorage.setItem('mfilm.camera', bodyFor(picker.value).platform); } catch {}
  location.search = q.toString();          // a fresh camera: its own card, its own roll
});
document.title = `M-Film · ${body.short}`;
const screen = cam.querySelector('.screen');
const statusEl = document.querySelector('.status');
const statusText = statusEl.querySelector('.status-text');
const steps = Object.fromEntries([...document.querySelectorAll('.steps li')].map((li) => [li.dataset.step, li]));

applyLang();
document.querySelector('.lang').addEventListener('click', () => { toggleLang(); say(lastStatus, ...lastArgs); });

const live = new LiveView(screen.querySelector('.lv'), {
  video: 'media/liveview.mp4',
  stills: ['img/samples/portra400.jpg', 'img/samples/gold200.jpg', 'img/samples/ektar100.jpg', 'img/samples/superia400.jpg'],
});
const camera = new Camera(screen.querySelector('.fos'), live);
window.mfilm = camera;     // for the console: mfilm.card, mfilm.roll

// ---------------------------------------------------------------- status and the guide

let lastStatus = 'st.boot', lastArgs = [];
function say(id, ...args) {
  lastStatus = id; lastArgs = args;
  statusText.textContent = T(id, ...args);
}
let developed = false;
// PLAY after a roll is developed: the last step done
camera.addEventListener('mode', (e) => {
  if (e.detail.ui && developed && lastKey === KEY.PLAY) stage('done');
});
let lastKey = 0;
const pressKey = camera.press.bind(camera);
camera.press = (k) => { lastKey = k; pressKey(k); };

function stage(name) {
  const order = ['load', 'shoot', 'develop', 'prints', 'done'];
  const at = order.indexOf(name);
  order.slice(0, 4).forEach((s, i) => {
    steps[s].classList.toggle('done', i < at);
    steps[s].classList.toggle('now', i === at);
  });
}
stage('load');

function rollStatus() {
  const r = camera.roll;
  if (!r) return say('st.noroll');
  if (r.shot >= r.exposures) return say('st.finished');
  say(body.dslr && !camera.lvOn ? 'st.plate' : 'st.roll', r.shot, r.exposures);
}

camera.addEventListener('mode', (e) => {
  statusEl.classList.toggle('live', !e.detail.ui);
  if (e.detail.ui) {
    const r = camera.roll;
    return say(camera.busy ? 'st.developing' : r && r.shot >= r.exposures ? 'st.finished' : r ? 'st.open' : 'st.menu');
  }
  rollStatus();
});
camera.addEventListener('loaded', () => { stage('shoot'); });
// a DSLR: LiveView with its LV button; the top plate on the back screen without it
const lvBtns = [...document.querySelectorAll('[data-ctl="lv"]')];
lvBtns.forEach((b) => {
  b.hidden = !body.dslr;
  b.addEventListener('click', () => { if (!camera.ui) camera.setLv(!camera.lvOn); });
});
camera.addEventListener('lv', (e) => {
  cam.classList.toggle('lv-on', !!e.detail.a);
  rollStatus();
});
camera.addEventListener('screen', (e) => {
  screen.classList.remove('flip-2', 'flip-3');
  if (e.detail.a >= 2) screen.classList.add('flip-' + e.detail.a);
});
cam.classList.toggle('lv-on', !body.dslr);
camera.addEventListener('shot', (e) => {
  cam.classList.add('shot-once');
  const { a: shot, b: exposures } = e.detail;
  say(body.dslr && !camera.lvOn ? 'st.plate' : 'st.roll', shot, exposures);
});
camera.addEventListener('finished', () => { stage('develop'); say('st.finished'); });
camera.addEventListener('developing', (e) => {
  statusEl.classList.toggle('work', !!e.detail.a);
  if (e.detail.a) say('st.developing');
  else { stage('prints'); say('st.developed'); developed = true; }
});
camera.addEventListener('crash', () => say('st.crash'));

// ---------------------------------------------------------------- the buttons

const press = (el, k) => {
  el.classList.add('down');
  camera.press(k);
};
const release = (el, k) => {
  el.classList.remove('down');
  camera.release(k);
};
for (const el of cam.querySelectorAll('[data-key]:not([data-key=""])')) {
  const k = KEY[el.dataset.key];
  el.addEventListener('pointerdown', (e) => { e.preventDefault(); el.setPointerCapture(e.pointerId); press(el, k); });
  el.addEventListener('pointerup', () => release(el, k));
  el.addEventListener('pointercancel', () => release(el, k));
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); if (!e.repeat) press(el, k); } });
  el.addEventListener('keyup', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); release(el, k); } });
}
for (const el of document.querySelectorAll('.mini[data-key]')) {
  el.addEventListener('click', () => { camera.press(KEY[el.dataset.key]); });
}

// the dials: the Quick Control Dial dragged round, or the mouse wheel over it (a click
// every 24 degrees); a DSLR's main dial by the shutter the same with the wheel
const dial = cam.querySelector('.dial.ring');
const ring = dial && dial.querySelector('.dial-ring');
let turn = 0, dragAngle = null, acc = 0;
const click = (dir) => {
  camera.press(dir > 0 ? KEY.WHEEL_R : KEY.WHEEL_L);
  turn += dir * 12;
  if (ring) ring.style.setProperty('--turn', `${turn}deg`);
};
if (ring) {
  const angleOf = (e) => {
    const r = dial.getBoundingClientRect();
    return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180 / Math.PI;
  };
  ring.addEventListener('pointerdown', (e) => {
    ring.setPointerCapture(e.pointerId);
    dragAngle = angleOf(e); acc = 0;
    dial.classList.add('turning');
  });
  ring.addEventListener('pointermove', (e) => {
    if (dragAngle === null) return;
    const a = angleOf(e);
    let d = a - dragAngle;
    if (d > 180) d -= 360;
    if (d < -180) d += 360;
    dragAngle = a; acc += d;
    while (acc >= 24) { click(1); acc -= 24; }
    while (acc <= -24) { click(-1); acc += 24; }
  });
  const endDrag = () => { dragAngle = null; dial.classList.remove('turning'); };
  ring.addEventListener('pointerup', endDrag);
  ring.addEventListener('pointercancel', endDrag);
}
for (const el of cam.querySelectorAll('.dial.ring, .topdial')) {
  let wheelAcc = 0;
  el.addEventListener('wheel', (e) => {
    e.preventDefault();
    wheelAcc += e.deltaY;
    while (wheelAcc >= 40) { click(1); wheelAcc -= 40; }
    while (wheelAcc <= -40) { click(-1); wheelAcc += 40; }
  }, { passive: false });
}

// the shutter: down is a half-press (the HUD lights, the film OS closes),
// up takes the picture; held, it keeps firing like a motor drive
const shutter = cam.querySelector('.ctl.shutter');
const blackout = screen.querySelector('.blackout');
let held = null;
camera.addEventListener('shutter', () => {
  blackout.classList.remove('on'); void blackout.offsetWidth; blackout.classList.add('on');
});
async function fire() {
  const r = await camera.fire();
  if (r === 'noroll') { say('st.noroll'); camera.open(OPEN.SHELF); }
  else if (r === 'locked' && camera.roll && camera.roll.shot >= camera.roll.exposures) say('st.finished');
  else if (r === 'locked' && !camera.ui) say('st.wind');
  return r;
}
function shutterDown() {
  if (held) return;
  shutter.classList.add('half');
  camera.half(true);
  held = { t: setTimeout(function burst() {
    shutter.classList.add('down');
    fire().then((r) => { if (held && r === 'shot') held.t = setTimeout(burst, 280); });
  }, 650), fired: false };
}
function shutterUp() {
  if (!held) return;
  const wasBurst = shutter.classList.contains('down');
  clearTimeout(held.t);
  held = null;
  shutter.classList.add('down');
  setTimeout(() => shutter.classList.remove('down', 'half'), 120);
  camera.half(false);
  if (!wasBurst) fire();
}
shutter.addEventListener('pointerdown', (e) => { e.preventDefault(); shutter.setPointerCapture(e.pointerId); shutterDown(); });
shutter.addEventListener('pointerup', shutterUp);
shutter.addEventListener('pointercancel', shutterUp);

// the power button: off and on again plays the boot
cam.querySelector('.ctl.power').addEventListener('click', () => camera.open(OPEN.BOOT));

// ---------------------------------------------------------------- the keyboard

const KEYMAP = {
  ArrowLeft: KEY.LEFT, ArrowRight: KEY.RIGHT, ArrowUp: KEY.UP, ArrowDown: KEY.DOWN,
  Enter: KEY.SET, m: KEY.MENU, M: KEY.MENU, i: KEY.INFO, I: KEY.INFO, p: KEY.PLAY, P: KEY.PLAY,
  Backspace: KEY.HOME, Delete: KEY.HOME, '[': KEY.WHEEL_L, ']': KEY.WHEEL_R,
};
const camInView = () => { const r = cam.getBoundingClientRect(); return r.bottom > 80 && r.top < innerHeight - 80; };
addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || !camInView()) return;
  if (e.target.closest('input, textarea, select, summary, a, .top, dialog') || document.querySelector('dialog[open]')) return;
  if (e.key === ' ') { e.preventDefault(); if (!e.repeat) shutterDown(); return; }
  const k = KEYMAP[e.key];
  if (k === undefined) return;
  e.preventDefault();
  if (k === KEY.WHEEL_L || k === KEY.WHEEL_R) return click(k === KEY.WHEEL_R ? 1 : -1);
  if (!e.repeat) camera.press(k);
});
addEventListener('keyup', (e) => {
  if (e.key === ' ') { shutterUp(); return; }
  const k = KEYMAP[e.key];
  if (k !== undefined && k !== KEY.WHEEL_L && k !== KEY.WHEEL_R) camera.release(k);
});

// ---------------------------------------------------------------- go

if (typeof WebAssembly !== 'object') {
  screen.querySelector('.loading span').textContent = T('st.nowasm');
  say('st.nowasm');
} else camera.start(body).then(() => {
  screen.querySelector('.loading').classList.add('gone');
  say('st.menu');
}).catch((e) => {
  console.error(e);
  screen.querySelector('.loading span').textContent = T('st.crash');
  say('st.crash');
});
