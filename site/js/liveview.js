// LiveView: what the camera's sensor sees, under the film OS's screen.
// A looping video (media/liveview.mp4) when there is one; until then a few
// stills, drifting as a hand-held camera does.

export class LiveView {
  constructor(canvas, { video, stills = [] } = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.video = null;
    this.stills = [];
    this.t0 = performance.now();
    this.brightness = 1;
    this.draw = this.draw.bind(this);
    if (video) this.tryVideo(video);
    for (const src of stills) {
      const img = new Image();
      img.decoding = 'async';
      img.src = src;
      img.onload = () => this.stills.push(img);
    }
    requestAnimationFrame(this.draw);
  }

  tryVideo(src) {
    const v = document.createElement('video');
    Object.assign(v, { src, muted: true, loop: true, playsInline: true, autoplay: true, crossOrigin: 'anonymous' });
    v.addEventListener('canplay', () => { this.video = v; v.play().catch(() => {}); }, { once: true });
    v.load();
  }

  // the picture, cropped to fill w x h, onto ctx
  paint(ctx, w, h, t) {
    if (this.video) return cover(ctx, this.video, this.video.videoWidth, this.video.videoHeight, w, h, 0, 0, 1);
    if (!this.stills.length) { ctx.fillStyle = '#111'; ctx.fillRect(0, 0, w, h); return; }
    t = Math.max(0, t);
    const per = 9000, i = Math.floor(t / per), f = (t % per) / per;
    const a = this.stills[i % this.stills.length], b = this.stills[(i + 1) % this.stills.length];
    // a slow hand-held drift: a little zoom and wander
    const dx = Math.sin(t / 2300) * 0.012 + Math.sin(t / 900) * 0.002;
    const dy = Math.cos(t / 2900) * 0.010 + Math.cos(t / 700) * 0.002;
    cover(ctx, a, a.naturalWidth, a.naturalHeight, w, h, dx, dy, 1.06 + f * 0.04);
    if (f > 0.9 && b !== a) {
      ctx.globalAlpha = (f - 0.9) / 0.1;
      cover(ctx, b, b.naturalWidth, b.naturalHeight, w, h, dx, dy, 1.06);
      ctx.globalAlpha = 1;
    }
  }

  draw(now) {
    const { width: w, height: h } = this.canvas;
    this.ctx.filter = this.brightness === 1 ? 'none' : `brightness(${this.brightness})`;
    this.paint(this.ctx, w, h, Math.max(0, now - this.t0));
    this.ctx.filter = 'none';
    requestAnimationFrame(this.draw);
  }

  // what is on show now, as the photo for a CR2: a colour PFM, linear sRGB
  // (0.18 = mid grey), rows bottom to top (sim/tools/mkcr2.c --image)
  capturePFM(w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    this.paint(ctx, w, h, performance.now() - this.t0);
    const px = ctx.getImageData(0, 0, w, h).data;
    const lin = new Float32Array(256);
    for (let i = 0; i < 256; i++) {
      const v = i / 255;
      lin[i] = v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    }
    const head = new TextEncoder().encode(`PF\n${w} ${h}\n-1.0\n`);
    const out = new Uint8Array(head.length + w * h * 12);
    out.set(head);
    const dv = new DataView(out.buffer, head.length);
    let o = 0;
    for (let y = h - 1; y >= 0; y--)
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        dv.setFloat32(o, lin[px[i]], true);
        dv.setFloat32(o + 4, lin[px[i + 1]], true);
        dv.setFloat32(o + 8, lin[px[i + 2]], true);
        o += 12;
      }
    return out;
  }
}

function cover(ctx, src, sw, sh, w, h, dx, dy, zoom) {
  if (!sw || !sh) return;
  const s = Math.max(w / sw, h / sh) * zoom;
  const dw = sw * s, dh = sh * s;
  ctx.drawImage(src, (w - dw) / 2 + dx * w, (h - dh) / 2 + dy * h, dw, dh);
}
