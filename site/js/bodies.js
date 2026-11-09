// Every camera M-Film runs on, as the page draws it from the back: its body,
// its screen, and each control where it sits, in the body's own coordinates.
// The EOS M is img/eosm-back.svg; the others are drawn here from their
// family's shape. Positions are close to the real cameras but drawn from
// memory: a photo can take a drawing's place (body.image), the controls
// staying where these numbers put them.
//
// What the film OS sees of each (web.c, web_config): the name, a DSLR (no
// LiveView until the LV button; the top plate on the back screen meanwhile),
// a screen that swivels (Screen orientation in Settings), and whether Magic
// Lantern can set exposure simulation there (not on the 600D and 1100D).

// ---------------------------------------------------------------- the cameras

// controls: [kind, x, y, extra]. kind is a key the film OS knows (MENU, INFO,
// PLAY, HOME = the trash/delete button, SET, LV, Q = SET in the film OS), or a
// part that is there to be seen (AE, AF, AFON, REC). dial: the 4-way keys with
// SET; ring: true where they sit in a Quick Control Dial that turns.
// top: the main dial by the shutter button, turned for the wheel on DSLRs.

const EOSM = {
  id: 'eosm', platform: 'EOSM.202', name: 'Canon EOS M', short: 'EOS M', family: 'mirrorless',
  view: [1100, 740], image: 'img/eosm-back.svg', screen: [60, 140, 680, 453],
  dslr: false, swivel: false, expsim: true,
  shutter: [900, 37, 88], power: [761, 55],
  dial: { x: 915, y: 400, r: 120, ring: true },
  controls: [['REC', 990, 150, 24], ['INFO', 830, 190, 27], ['HOME', 1000, 250, 24], ['PLAY', 830, 600, 27], ['MENU', 1000, 600, 27]],
};

function rebel(id, platform, name, short, o = {}) {
  const q = o.q !== false;
  return {
    id, platform, name, short, family: 'rebel', view: [1200, 840], screen: [80, 272, 690, 460],
    dslr: true, swivel: !!o.swivel, expsim: o.expsim !== false, small: !!o.small,
    hump: [380, 700], shutter: [1090, 48, 92], power: [930, 70], top: [985, 92, 120],
    dial: { x: 985, y: 485, r: 112, ring: false },
    controls: [
      ['MENU', 130, 180, 30, 'pill'], ['INFO', 250, 180, 30, 'pill'], ['LV', 800, 185, 30],
      ['AE', 990, 175, 26], ['AF', 1100, 175, 26],
      ...(q ? [['Q', 875, 315, 28]] : []),
      ['PLAY', 875, 680, 28], ['HOME', 1095, 680, 28],
    ],
  };
}

function mid(id, platform, name, short, o = {}) {
  return {
    id, platform, name, short, family: 'mid', view: [1260, 880], screen: [90, 300, 690, 460],
    dslr: true, swivel: !!o.swivel, expsim: true,
    hump: [380, 720], shutter: [1140, 48, 96], power: [80, 102], top: [1030, 96, 130],
    dial: { x: 1035, y: 545, r: 150, ring: true },
    controls: [
      ['MENU', 150, 205, 30, 'pill'], ['INFO', 270, 205, 30, 'pill'], ['LV', 860, 210, 34],
      ['AFON', 980, 185, 28], ['AE', 1080, 185, 26], ['AF', 1175, 185, 26],
      ['Q', 880, 345, 30], ['PLAY', 875, 790, 28], ['HOME', 1035, 790, 28],
    ],
  };
}

function pro(id, platform, name, short, o = {}) {
  const left = o.q ? [['MENU', 115, 330], ['INFO', 115, 420], ['Q', 115, 510], ['PLAY', 115, 640], ['HOME', 115, 730]]
                   : [['MENU', 115, 340], ['INFO', 115, 440], ['PLAY', 115, 640], ['HOME', 115, 740]];
  return {
    id, platform, name, short, family: 'pro', view: [1320, 900], screen: [210, 310, 660, 440],
    dslr: true, swivel: false, expsim: true,
    hump: [420, 760], shutter: [1200, 50, 100], power: [1150, 830], top: [1090, 98, 130],
    dial: { x: 1080, y: 590, r: 160, ring: true },
    joystick: [1080, 330],
    controls: [
      ...left.map(([k, x, y]) => [k, x, y, 30, 'pill']),
      ['LV', 900, 200, 34], ['AFON', 1030, 180, 28], ['AE', 1140, 180, 26], ['AF', 1240, 180, 26],
    ],
  };
}

export const BODIES = [
  EOSM,
  mid('6d', '6D.116', 'Canon EOS 6D', '6D'),
  mid('60d', '60D.111', 'Canon EOS 60D', '60D', { swivel: true }),
  mid('70d', '70D.112', 'Canon EOS 70D', '70D', { swivel: true }),
  pro('5d3', '5D3.123', 'Canon EOS 5D Mark III', '5D Mark III', { q: true }),
  pro('5d2', '5D2.212', 'Canon EOS 5D Mark II', '5D Mark II'),
  pro('50d', '50D.109', 'Canon EOS 50D', '50D'),
  rebel('100d', '100D.101', 'Canon EOS 100D', '100D / SL1', { small: true }),
  rebel('500d', '500D.111', 'Canon EOS 500D', '500D / T1i', { q: false }),
  rebel('550d', '550D.109', 'Canon EOS 550D', '550D / T2i'),
  rebel('600d', '600D.102', 'Canon EOS 600D', '600D / T3i', { swivel: true, expsim: false }),
  rebel('650d', '650D.104', 'Canon EOS 650D', '650D / T4i', { swivel: true }),
  rebel('700d', '700D.115', 'Canon EOS 700D', '700D / T5i', { swivel: true }),
  rebel('1100d', '1100D.105', 'Canon EOS 1100D', '1100D / T3', { expsim: false }),
];

export function bodyFor(id) {
  return BODIES.find((b) => b.id === id) || EOSM;
}

// ---------------------------------------------------------------- drawing a DSLR

const DEFS = `
  <defs>
    <linearGradient id="g-body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#3d3b39"/><stop offset=".06" stop-color="#2e2d2b"/>
      <stop offset=".55" stop-color="#232220"/><stop offset="1" stop-color="#161514"/>
    </linearGradient>
    <linearGradient id="g-side" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000" stop-opacity=".45"/><stop offset=".06" stop-color="#000" stop-opacity="0"/>
      <stop offset=".94" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".5"/>
    </linearGradient>
    <linearGradient id="g-prism" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4a4845"/><stop offset=".25" stop-color="#33312f"/><stop offset="1" stop-color="#262523"/>
    </linearGradient>
    <linearGradient id="g-metal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#9b9893"/><stop offset=".5" stop-color="#5d5a56"/><stop offset="1" stop-color="#3a3836"/>
    </linearGradient>
    <linearGradient id="g-top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#5a5754"/><stop offset="1" stop-color="#242322"/>
    </linearGradient>
    <linearGradient id="g-glass" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0c0c0d"/><stop offset="1" stop-color="#050506"/>
    </linearGradient>
    <radialGradient id="g-well" cx=".5" cy=".42" r=".6">
      <stop offset=".72" stop-color="#121111"/><stop offset="1" stop-color="#3f3d3a"/>
    </radialGradient>
    <radialGradient id="g-cup" cx=".5" cy=".4" r=".7">
      <stop offset="0" stop-color="#1d1c1b"/><stop offset=".8" stop-color="#121211"/><stop offset="1" stop-color="#2b2a28"/>
    </radialGradient>
    <!-- Canon's leatherette: a fine pebble grain -->
    <pattern id="g-pebble" width="9" height="9" patternUnits="userSpaceOnUse">
      <rect width="9" height="9" fill="#1b1a19"/>
      <circle cx="2" cy="2" r="1.6" fill="#262524"/><circle cx="6.5" cy="5" r="1.8" fill="#242322"/>
      <circle cx="3" cy="7.2" r="1.3" fill="#292827"/>
    </pattern>
    <filter id="g-grain" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="1.3" numOctaves="2" seed="7"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .045 0"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
    <filter id="g-soft"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>`;

// the body outline: the shoulders, the prism housing in a smooth rise, rounded corners, the grip a
// little fuller on the right and the bottom gently curved
function outline(b) {
  const [W, H] = b.view, [h0, h1] = b.hump, top = 120, r = 74, peak = 14;
  const rise = Math.min(90, (h1 - h0) * .26);
  return `M ${r} ${top}
    H ${h0 - 30}
    C ${h0 + 10} ${top} ${h0 + rise * .4} ${peak + 30} ${h0 + rise} ${peak + 8}
    Q ${h0 + rise + 14} ${peak} ${h0 + rise + 40} ${peak}
    H ${h1 - rise - 40}
    Q ${h1 - rise - 14} ${peak} ${h1 - rise} ${peak + 8}
    C ${h1 - rise * .4} ${peak + 30} ${h1 - 10} ${top} ${h1 + 30} ${top}
    H ${W - r - 30}
    C ${W - 20} ${top - 8} ${W - 4} ${top + 20} ${W - 4} ${top + r}
    V ${H - r - 10}
    C ${W - 4} ${H - 20} ${W - 40} ${H - 4} ${W - r - 10} ${H - 4}
    Q ${W / 2} ${H + 6} ${r + 10} ${H - 4}
    C ${40} ${H - 4} ${6} ${H - 20} ${6} ${H - r - 10}
    V ${top + r}
    C ${6} ${top + 20} ${20} ${top} ${r} ${top} Z`;
}

const TOP = 120;

export function dslrSvg(b) {
  const [W, H] = b.view, [sx, sy, sw, sh] = b.screen, [h0, h1] = b.hump;
  const cx = (h0 + h1) / 2;
  const cupW = (h1 - h0) * .62, cupH = 150, cupX = cx - cupW / 2, cupY = 28;
  const [tx, ty, tw] = b.top;
  const grip = W - (b.family === 'pro' ? 250 : 230);
  // the mode dial: on the left shoulder on the bigger bodies, to the right of the prism on the Rebels
  const md = b.family === 'rebel' ? [h1 + 85, TOP - 8, 150] : [h0 - 150, TOP - 8, 170];
  const wells = [
    ...b.controls.map(([, x, y, r = 28, shape]) => shape === 'pill'
      ? `<rect x="${x - r * 1.3 - 8}" y="${y - r * .62 - 8}" width="${r * 2.6 + 16}" height="${r * 1.24 + 16}" rx="${r * .62 + 8}" fill="url(#g-well)"/>`
      : `<circle cx="${x}" cy="${y}" r="${r + 8}" fill="url(#g-well)"/>`),
    b.dial ? `<circle cx="${b.dial.x}" cy="${b.dial.y}" r="${b.dial.r + 16}" fill="url(#g-well)"/>` : '',
    b.joystick ? `<circle cx="${b.joystick[0]}" cy="${b.joystick[1]}" r="54" fill="url(#g-well)"/>` : '',
  ].join('');
  const labels = b.controls.filter(([k]) => k === 'MENU' || k === 'INFO').map(([k, x, y, r = 28]) =>
    `<text x="${x}" y="${y - r - 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#cfc9c0" letter-spacing="1">${k === 'INFO' ? 'INFO.' : k}</text>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">${DEFS}
    <!-- behind the top edge: the mode dial, the main dial and the shutter button's collar -->
    <g>
      <rect x="${md[0] - md[2] / 2}" y="${md[1] - 46}" width="${md[2]}" height="50" rx="12" fill="url(#g-top)"/>
      ${Array.from({ length: 22 }, (_, i) => `<rect x="${md[0] - md[2] / 2 + 6 + i * (md[2] - 12) / 22}" y="${md[1] - 42}" width="3" height="40" fill="#1a1918" opacity=".7"/>`).join('')}
      <rect x="${tx - tw / 2 - 10}" y="${ty - 46}" width="${tw + 20}" height="44" rx="10" fill="#2a2928"/>
      <ellipse cx="${b.shutter[0]}" cy="${b.shutter[1] + 38}" rx="${b.shutter[2] * .78}" ry="20" fill="url(#g-top)"/>
    </g>
    <!-- the hot shoe on the prism -->
    <rect x="${cx - 70}" y="2" width="140" height="22" rx="4" fill="url(#g-metal)"/>
    <rect x="${cx - 52}" y="8" width="104" height="10" rx="2" fill="#1d1c1b"/>
    <!-- the body -->
    <path d="${outline(b)}" fill="url(#g-body)"/>
    <path d="${outline(b)}" fill="url(#g-side)"/>
    <!-- leatherette on the grip and the thumb rest -->
    <path d="M ${grip} ${TOP + 70} Q ${W - 70} ${TOP + 40} ${W - 22} ${TOP + 110} V ${H - 90} Q ${W - 40} ${H - 30} ${grip + 30} ${H - 40} Q ${grip - 30} ${H / 2} ${grip} ${TOP + 70} Z"
          fill="url(#g-pebble)" opacity=".85"/>
    <path d="${outline(b)}" fill="#fff" filter="url(#g-grain)"/>
    <!-- the light catching the top edge and the prism -->
    <path d="M 70 ${TOP + 3} H ${h0 - 30}" stroke="#6d6964" stroke-width="2.5" opacity=".55" stroke-linecap="round"/>
    <path d="M ${h1 + 30} ${TOP + 3} H ${W - 110}" stroke="#6d6964" stroke-width="2.5" opacity=".55" stroke-linecap="round"/>
    <path d="M ${h0 + 60} ${24} H ${h1 - 60}" stroke="#77736e" stroke-width="2" opacity=".5" stroke-linecap="round"/>
    <path d="${outline(b)}" fill="none" stroke="#4d4a47" stroke-width="2" opacity=".55"/>
    <!-- metal strap lugs -->
    <path d="M 0 ${TOP + 40} l 18 -10 v 70 l -18 -10 z" fill="url(#g-metal)"/>
    <path d="M ${W} ${TOP + 40} l -18 -10 v 70 l 18 -10 z" fill="url(#g-metal)"/>
    <!-- the eyepiece: a rubber cup, the finder's glass, the diopter wheel beside it -->
    <rect x="${cupX - 10}" y="${cupY - 8}" width="${cupW + 20}" height="${cupH + 22}" rx="46" fill="#0e0e0e" filter="url(#g-soft)" opacity=".8"/>
    <rect x="${cupX}" y="${cupY}" width="${cupW}" height="${cupH}" rx="40" fill="url(#g-cup)" stroke="#2f2e2c" stroke-width="3"/>
    <rect x="${cupX + cupW * .2}" y="${cupY + 32}" width="${cupW * .6}" height="${cupH - 64}" rx="10" fill="#030303" stroke="#1a1a1a" stroke-width="3"/>
    <rect x="${cupX + cupW * .2 + 8}" y="${cupY + 38}" width="${cupW * .25}" height="10" rx="4" fill="#fff" opacity=".07"/>
    <rect x="${cupX + cupW + 16}" y="${cupY + 40}" width="16" height="64" rx="5" fill="#2b2a28"/>
    ${Array.from({ length: 7 }, (_, i) => `<rect x="${cupX + cupW + 16}" y="${cupY + 44 + i * 9}" width="16" height="3" fill="#151413"/>`).join('')}
    <!-- the thumb rest's rubber -->
    <path d="M ${W - 180} ${TOP + 230} q 90 -20 150 40 v 140 q -70 20 -150 -20 z" fill="url(#g-pebble)" opacity=".6"/>
    ${b.swivel ? `<rect x="${sx - 58}" y="${sy + 30}" width="22" height="${sh - 60}" rx="9" fill="#232221" stroke="#3a3836"/>
                  <rect x="${sx - 54}" y="${sy + 50}" width="14" height="${sh - 100}" rx="6" fill="#191817"/>` : ''}
    <!-- the screen: bezel and glass -->
    <rect x="${sx - 20}" y="${sy - 20}" width="${sw + 40}" height="${sh + 40}" rx="${b.swivel ? 24 : 14}" fill="#0b0b0b" stroke="#3f3c39" stroke-width="2"/>
    <rect x="${sx}" y="${sy}" width="${sw}" height="${sh}" rx="2" fill="url(#g-glass)"/>
    ${wells}
    ${labels}
    <!-- the speaker, and the card door's seam on the grip -->
    <g fill="#0d0d0d">${Array.from({ length: 12 }, (_, i) => `<circle cx="${sx + sw + 70 + (i % 4) * 14}" cy="${H - 70 + Math.floor(i / 4) * 14}" r="3.4"/>`).join('')}</g>
    <path d="M ${W - 34} ${H - 260} V ${H - 90}" stroke="#0e0e0d" stroke-width="2" opacity=".8"/>
    <!-- the access lamp -->
    ${b.dial ? `<circle cx="${b.dial.x + b.dial.r * .9}" cy="${b.dial.y + b.dial.r + 50}" r="5" fill="#2c1a0e" stroke="#4a3a2a"/>` : ''}
  </svg>`;
}

// ---------------------------------------------------------------- the controls

const LABEL = { MENU: 'MENU', INFO: 'INFO', PLAY: '▶', HOME: '⌫', Q: 'Q', LV: '', AE: '✱', AF: '⊞', AFON: 'AF-ON', REC: '' };
const ARIA = {
  MENU: 'MENU', INFO: 'INFO', PLAY: 'Playback', HOME: 'Delete (opens M-Film home)', Q: 'Q (SET in M-Film)',
  LV: 'LiveView on/off', AE: 'AE lock (unused)', AF: 'AF point (unused)', AFON: 'AF-ON (unused)', REC: 'Movie (unused)',
};
const KEYOF = { MENU: 'MENU', INFO: 'INFO', PLAY: 'PLAY', HOME: 'HOME', Q: 'SET' };

// MENU and INFO are printed on a DSLR's body (dslrSvg), on the EOS M's buttons
const printed = (b, kind) => !b.image && (kind === 'MENU' || kind === 'INFO');

// the camera's buttons over the drawing, each in % of the body
export function buildCamera(cam, b) {
  const [W, H] = b.view;
  const px = (x) => `${(x / W) * 100}%`, py = (y) => `${(y / H) * 100}%`, pw = (w) => `${(w / W) * 100}%`;
  cam.style.aspectRatio = `${W} / ${H}`;
  cam.dataset.model = b.id;
  cam.dataset.family = b.family;
  cam.classList.toggle('dslr', b.dslr);
  if (b.small) cam.style.maxWidth = '880px';

  const img = cam.querySelector('.body');
  if (b.image) img.src = b.image;
  else img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(dslrSvg(b));
  img.alt = `${b.name}, from the back`;

  const scr = cam.querySelector('.screen');
  const [sx, sy, sw, sh] = b.screen;
  Object.assign(scr.style, { left: px(sx), top: py(sy), width: pw(sw), height: py(sh) });

  const add = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return cam.appendChild(t.content.firstChild); };
  const place = (el, x, y, w) => Object.assign(el.style, { left: px(x), top: py(y), width: pw(w) });

  place(add(`<button class="ctl shutter" data-ctl="shutter" aria-label="Shutter button (hold to half-press)"><span></span></button>`), b.shutter[0], b.shutter[1], b.shutter[2]);
  place(add(`<button class="ctl power" data-ctl="power" aria-label="Power"></button>`), b.power[0], b.power[1], 56);

  for (const [kind, x, y, r = 28, shape] of b.controls) {
    const key = KEYOF[kind];
    const el = add(`<button class="ctl ${kind.toLowerCase()} ${shape || 'round'}" aria-label="${ARIA[kind]}"
      ${key ? `data-key="${key}"` : ''} ${kind === 'LV' ? 'data-ctl="lv"' : ''}>${printed(b, kind) ? '' : LABEL[kind] ?? kind}</button>`);
    place(el, x, y, (shape === 'pill' ? 2.6 : 2) * r);
    if (!key && kind !== 'LV') el.classList.add('deco');
  }

  if (b.dial) {
    const d = add(`<div class="dial ${b.dial.ring ? 'ring' : 'cross'}" role="group" aria-label="${b.dial.ring ? 'Quick Control Dial: turn it, or press its edges' : 'Cross keys'}">
        ${b.dial.ring ? '<div class="dial-ring"></div>' : ''}
        <button class="ctl dpad up" data-key="UP" aria-label="Up"></button>
        <button class="ctl dpad right" data-key="RIGHT" aria-label="Right"></button>
        <button class="ctl dpad down" data-key="DOWN" aria-label="Down"></button>
        <button class="ctl dpad left" data-key="LEFT" aria-label="Left"></button>
        <button class="ctl set" data-key="SET" aria-label="SET">SET</button>
      </div>`);
    place(d, b.dial.x, b.dial.y, 2 * b.dial.r);
  }
  if (b.joystick) {
    const j = add(`<div class="dial stick" role="group" aria-label="Multi-controller">
        <button class="ctl dpad up" data-key="UP" aria-label="Up"></button>
        <button class="ctl dpad right" data-key="RIGHT" aria-label="Right"></button>
        <button class="ctl dpad down" data-key="DOWN" aria-label="Down"></button>
        <button class="ctl dpad left" data-key="LEFT" aria-label="Left"></button>
        <button class="ctl set" data-key="SET" aria-label="Press the multi-controller (SET)"></button>
      </div>`);
    place(j, b.joystick[0], b.joystick[1], 92);
  }
  if (b.top) {
    const t = add(`<div class="topdial" role="group" aria-label="Main dial: turn it">
        <button class="ctl" data-key="WHEEL_L" aria-label="Main dial left"></button>
        <button class="ctl" data-key="WHEEL_R" aria-label="Main dial right"></button>
      </div>`);
    place(t, b.top[0], b.top[1] - 23, b.top[2]);
  }
}
