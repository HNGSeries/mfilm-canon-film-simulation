// check.js films.json page.html: the page's darkroom against the camera's own prints (printdump),
// at the screen's size and Medium, for frames shot level and upright. The dumps and prints are in build/.
const fs = require("fs"), path = require("path");
const dir = path.join(__dirname, "build");
function pipeline(file) {
  const s = fs.readFileSync(file, "utf8");
  const a = s.indexOf("/* ---------------------------------------------------------------- the darkroom, as fos_dev.c */");
  const b = s.indexOf("/* ---------------------------------------------------------------- the controls */");
  const names = ["W", "H", "scannerEv", "expose", "lutApply", "trimTable", "halTint"];
  return new Function(s.slice(a, b) + "\nreturn {" + names.join(",") + "};")();
}
const u16 = f => { const b = fs.readFileSync(path.join(dir, f)); return new Uint16Array(b.buffer, b.byteOffset, b.length / 2); };
const u8 = f => new Uint8Array(fs.readFileSync(path.join(dir, f)));
const films = JSON.parse(fs.readFileSync(process.argv[2], "utf8")), P = pipeline(process.argv[3]);
const W = 720, H = 480, zeros = new Proxy({}, { get: () => 0 });
// name, the dumps, the picture on the screen's print (first column, width), the Medium print, the camera's prints
const CASES = [
  ["SAMPLE.CR2 (EOS M)", "street_s.u16", "street_m.u16", 0, 720, 1728, 1152, k => "ref_" + k, ["portra400", "cinestill800t", "velvia50", "hp5", "ektar100"]],
  ["_MG_0120 (650D)", "p0120_s.u16", "p0120_m.u16", 0, 720, 1728, 1152, k => "ref650_0120_" + k, ["portra400", "cinestill800t", "velvia50"]],
  ["_MG_0080 (650D, upright)", "p0080_s.u16", "p0080_m.u16", 200, 320, 1152, 1728, k => "ref650_0080_" + k, ["portra400", "cinestill800t", "velvia50"]],
];
let worst = 0;
for (const [name, fs_, fm, x0, pw, bw, bh, ref, keys] of CASES) {
  const lin = u16(fs_);
  let view = lin;
  if (pw !== W) { view = new Uint16Array(pw * H * 3); for (let y = 0; y < H; y++) view.set(lin.subarray(3 * (y * W + x0), 3 * (y * W + x0 + pw)), 3 * y * pw); }
  const scene = { id: name, lin, x0, pw, ev: P.scannerEv(lin, x0, pw), small: { w: pw, h: H, lin: view, x0, pw, screen: true } };
  scene.big = { w: bw, h: bh, lin: u16(fm), x0, pw, screen: false };
  console.log(`${name}: scanner ${scene.ev.toFixed(3)} EV`);
  for (const key of keys) {
    const film = films.find(f => f.key === key), table = P.trimTable(u8("look_" + key + ".bin"), zeros, film.mono);
    const look = { ev: film.ev, halation: film.halation, hal_thr: film.hal_thr, hal_tint: P.halTint(film, 0) };
    const res = [];
    for (const [pic, file] of [[scene.small, ref(key) + "_s.rgb"], [scene.big, ref(key) + "_m.rgb"]]) {
      const n = pic.w * pic.h, pos = new Uint16Array(n * 3), out = new Uint8Array(n * 3);
      const t0 = performance.now();
      P.expose(scene, film, look, pic, pos);
      for (let i = 0; i < n * 3; i += 3) P.lutApply(table, pos[i], pos[i + 1], pos[i + 2], out, i);
      const ms = performance.now() - t0;
      let cam = u8(file);
      if (pic.screen && pw !== W) { const c = new Uint8Array(pw * H * 3); for (let y = 0; y < H; y++) c.set(cam.subarray(3 * (y * W + x0), 3 * (y * W + x0 + pw)), 3 * y * pw); cam = c; }
      let diff = 0, max = 0;
      for (let i = 0; i < out.length; i++) { const d = Math.abs(out[i] - cam[i]); if (d) { diff++; if (d > max) max = d; } }
      if (max > worst) worst = max;
      res.push(`${pic.w} x ${pic.h}: ${diff ? diff + " of " + out.length + " differ, by at most " + max : "identical"} (${ms.toFixed(0)} ms)`);
    }
    console.log(`  ${key.padEnd(14)} ${res.join("; ")}`);
  }
}
console.log(worst <= 1 ? "PASS: nothing differs by more than one level" : "FAIL: a difference of " + worst);
process.exit(worst <= 1 ? 0 : 1);
