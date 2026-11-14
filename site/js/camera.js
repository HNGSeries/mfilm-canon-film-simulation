// Runs the film OS (fos/mfilm.wasm, built by ml-dev/filmos/web/build.sh) in
// the page: its screen onto a canvas over LiveView, the camera's keys into
// it, and the shutter writing CR2s onto the card for the darkroom.

import { Card, Wasi, WasiExit } from './wasi.js';

export const FOS_W = 720, FOS_H = 480;
export const KEY = {
  LEFT: 1, RIGHT: 2, UP: 3, DOWN: 4, WHEEL_L: 5, WHEEL_R: 6,
  SET: 7, MENU: 8, INFO: 9, PLAY: 10, HOME: 11, RELEASE: 0x100,
};
export const OPEN = { SHELF: 0, HOME: 1, BOOT: 2, BOOT_LV: 3, PRINTS: 4, END: 5, DARKROOM: 6 };
export const EVENT = ['loaded', 'shot', 'finished', 'rewound', 'developing', 'wind', 'lv', 'screen'];

const BASE = new URL('../fos/', import.meta.url);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const frame = () => new Promise((r) => requestAnimationFrame(r));

export class Camera extends EventTarget {
  constructor(canvas, liveview) {
    super();
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.image = this.ctx.createImageData(FOS_W, FOS_H);
    this.rgba = new Uint32Array(this.image.data.buffer);
    this.lut = new Uint32Array(256);
    this.live = liveview;
    this.card = new Card();
    this.tables = new Map();    // the colour tables asked for: LOOKnn.LUT -> a promise, done once it is on the card
    this.dirty = false;
    this.ui = false;
    this.busy = false;
  }

  // body: which camera (js/bodies.js): its name, DSLR or not, swivel screen, exposure simulation
  async start(body = {}) {
    const [mfilm, mkcr2, font, films] = await Promise.all([
      WebAssembly.compileStreaming(fetch(new URL('mfilm.wasm', BASE))),
      WebAssembly.compileStreaming(fetch(new URL('mkcr2.wasm', BASE))),
      fetch(new URL('FOSFONT.BIN', BASE)).then((r) => r.arrayBuffer()),
      fetch(new URL('FOSFILMS.BIN', BASE)).then((r) => r.arrayBuffer()),
    ]);
    this.mkcr2 = mkcr2;
    this.card.write('out/FOSFONT.BIN', new Uint8Array(font));
    this.card.write('out/FOSFILMS.BIN', new Uint8Array(films));
    this.card.mkdirs('card/DCIM/100CANON');
    this.card.mkdirs('card/ML');

    // the card's root (sim/port_files.c reads FOS_CARD)
    const wasi = new Wasi(this.card, { env: { FOS_CARD: '/card/' }, onOut: (s) => this.log(s) });
    let rewinding = false, wake = null, hold = null;
    const cam = this;
    const web = {
      sleep(ms, presented) {
        if (rewinding) { cam.ex.asyncify_stop_rewind(); rewinding = false; return; }
        cam.ex.asyncify_start_unwind(cam.asyncPtr);
        wake = presented ? (ms > 20 ? sleep(ms - 16).then(frame) : frame()) : sleep(Math.max(ms, 1));
      },
      now: () => Math.floor(performance.now()),
      present() { cam.dirty = true; },
      palette() { cam.loadPalette(); },
      mode(ui) {
        cam.ui = !!ui;
        cam.dispatchEvent(new CustomEvent('mode', { detail: { ui: cam.ui } }));
      },
      log(ptr) { cam.log(cam.cstr(ptr)); },
      clock(buf, size, withDate) {
        const d = new Date(), p = (n) => String(n).padStart(2, '0');
        const s = (withDate ? `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ` : '') + `${p(d.getHours())}:${p(d.getMinutes())}`;
        const b = new TextEncoder().encode(s).subarray(0, size - 1);
        const u8 = new Uint8Array(cam.memory.buffer);
        u8.set(b, buf); u8[buf + b.length] = 0;
      },
      event(what, a, b) {
        if (what === 0) cam.table(a);                   // a roll is loaded: its film's colour table
        if (what === 4) cam.busy = !!a;
        // developing starts: not before the tables asked for are on the card (a slow connection),
        // but not for ever either: without one the darkroom says which film has no table
        if (what === 4 && a) hold = Promise.race([Promise.all(cam.tables.values()), sleep(10000)]);
        cam.dispatchEvent(new CustomEvent(EVENT[what] || 'event', { detail: { a, b } }));
      },
    };
    const inst = await WebAssembly.instantiate(mfilm, { wasi_snapshot_preview1: wasi.imports(), web });
    this.ex = inst.exports;
    this.memory = this.ex.memory;
    wasi.bind(this.memory);
    this.ex._initialize();
    this.asyncPtr = this.ex.web_async();
    this.ex.web_init();
    if (body.name) {
      const b = new TextEncoder().encode(body.name.slice(0, 46));
      const u8 = new Uint8Array(this.memory.buffer, this.ex.web_model(), 48);
      u8.set(b); u8[b.length] = 0;
      this.ex.web_config(body.dslr ? 1 : 0, body.swivel ? 1 : 0, body.expsim === false ? 0 : 1);
    }
    this.loadPalette();

    this.render = this.render.bind(this);
    requestAnimationFrame(this.render);

    // the film OS's loop: each web.sleep unwinds back here and is resumed later
    (async () => {
      this.ex.web_main();
      while (this.ex.asyncify_get_state() === 1) {
        this.ex.asyncify_stop_unwind();
        await wake;
        if (hold) { await hold; hold = null; }
        rewinding = true;
        this.ex.asyncify_start_rewind(this.asyncPtr);
        this.ex.web_main();
      }
    })().catch((e) => { console.error(e); this.dispatchEvent(new CustomEvent('crash', { detail: e })); });
  }

  log(s) { if (this.debug) console.debug('[fos]', s); }
  cstr(ptr) {
    const u8 = new Uint8Array(this.memory.buffer);
    let end = ptr;
    while (u8[end]) end++;
    return new TextDecoder().decode(u8.subarray(ptr, end));
  }

  // A film's colour table onto the card, where the darkroom looks for it (ML/DARKROOM/LOOKnn.LUT,
  // nn the film's place on the shelf): the darkroom makes none itself, and a frame whose film has
  // none fails with "no colour table". About 100 KB a film, so only the films that are loaded.
  // A table that couldn't be fetched is asked for again the next time.
  table(film) {
    const name = `LOOK${String(film).padStart(2, '0')}.LUT`;
    if (!this.tables.has(name)) {
      this.tables.set(name, fetch(new URL(`tables/${name}`, BASE))
        .then((r) => { if (!r.ok) throw new Error(`${name}: ${r.status}`); return r.arrayBuffer(); })
        .then((b) => { this.card.write(`card/ML/DARKROOM/${name}`, new Uint8Array(b)); })
        .catch((e) => { this.tables.delete(name); console.error('no colour table:', e); }));
    }
    return this.tables.get(name);
  }

  loadPalette() {
    const pal = new Uint32Array(this.memory.buffer, this.ex.web_pal(), 256);
    for (let i = 0; i < 256; i++) {
      const c = pal[i];
      // ImageData is RGBA in memory: little-endian ABGR as a u32
      this.lut[i] = i === 0 ? 0 : (0xFF000000 | (c & 0xFF) << 16 | (c & 0xFF00) | (c >> 16 & 0xFF)) >>> 0;
    }
    this.dirty = true;
  }

  render() {
    if (this.dirty) {
      this.dirty = false;
      const px = new Uint8Array(this.memory.buffer, this.ex.web_screen(), FOS_W * FOS_H);
      const out = this.rgba, lut = this.lut;
      for (let i = 0; i < px.length; i++) out[i] = lut[px[i]];
      this.ctx.putImageData(this.image, 0, 0);
    }
    requestAnimationFrame(this.render);
  }

  // ---------------------------------------------------------------- keys

  key(k) { this.ex && this.ex.web_key(k); }
  press(k) { this.key(k); }
  release(k) { this.key(k | KEY.RELEASE); }
  open(screen) { this.ex && this.ex.web_open(screen); }

  get roll() {
    if (!this.ex) return null;
    const exp = this.ex.web_roll_exposures();
    return exp ? { shot: this.ex.web_roll_shot(), exposures: exp, film: this.cstr(this.ex.web_roll_film()) } : null;
  }

  // ---------------------------------------------------------------- the shutter

  half(down) { this.ex && this.ex.web_half(down ? 1 : 0); }

  // a DSLR's LiveView (the EOS M is always in it)
  get lvOn() { return this.ex ? !!this.ex.web_lv_on() : true; }
  setLv(on) { this.ex && this.ex.web_lv(on ? 1 : 0); }

  // returns 'shot', 'noroll', 'locked' (finished, wind lever, film OS up) or 'busy'
  async fire() {
    if (!this.ex || this.firing) return 'busy';
    if (this.ui) return 'locked';
    const n = this.ex.web_shot_begin();
    if (!n) return this.roll ? 'locked' : 'noroll';
    this.firing = true;
    try {
      this.dispatchEvent(new Event('shutter'));
      await frame();
      const pfm = this.live.capturePFM(864, 576);
      this.card.write('tmp/shot.pfm', pfm);
      const name = `/card/DCIM/100CANON/IMG_${String(n).padStart(4, '0')}.CR2`;
      this.runTool(this.mkcr2, ['mkcr2', name, '--small', '--image', '/tmp/shot.pfm', '--seed', String(n)]);
      this.card.nodes.delete('tmp/shot.pfm');
      this.ex.web_shot_end();
      return 'shot';
    } finally {
      this.firing = false;
    }
  }

  runTool(module, args) {
    const wasi = new Wasi(this.card, { args, onOut: (s) => this.log(s) });
    const inst = new WebAssembly.Instance(module, { wasi_snapshot_preview1: wasi.imports() });
    wasi.bind(inst.exports.memory);
    try { inst.exports._start(); } catch (e) { if (!(e instanceof WasiExit) || e.code) throw e; }
  }
}
