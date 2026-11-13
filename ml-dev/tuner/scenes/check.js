// check.js: the page's darkroom against the camera's own prints (printdump), at the screen's size and Medium
const fs = require("fs"), path = require("path");
const dir = path.join(__dirname, "build");
function pipeline(file) {
  const s = fs.readFileSync(file, "utf8");
  const a = s.indexOf("/* ---------------------------------------------------------------- the darkroom, as fos_dev.c */");
  const b = s.indexOf("/* ---------------------------------------------------------------- the controls */");
  const js = s.slice(a, b);
  const names = ["W", "H", "scannerEv", "expose", "lutApply", "trimTable", "halTint"];
  return new Function(js + "\nreturn {" + names.join(",") + "};")();
}
const u16 = f => { const b = fs.readFileSync(path.join(dir, f)); return new Uint16Array(b.buffer, b.byteOffset, b.length / 2); };
const u8 = f => new Uint8Array(fs.readFileSync(path.join(dir, f)));
const films = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const P = pipeline(process.argv[3]), OLD = process.argv[4] ? pipeline(process.argv[4]) : null;
const small = u16("street_s.u16"), bigLin = u16("street_m.u16"), BW = 1728, BH = 1152;
const scene = { id: "street", w: 720, h: 480, lin: small, ev: P.scannerEv(small), big: { w: BW, h: BH, lin: bigLin } };
console.log("scanner EV", scene.ev.toFixed(4));
const zeros = new Proxy({}, { get: () => 0 });
function develop(pl, film, pic, table, legacy) {
  const look = { ev: film.ev, halation: film.halation, hal_thr: film.hal_thr, hal_tint: pl.halTint(film, 0) };
  const n = pic.w * pic.h, pos = new Uint16Array(n * 3), out = new Uint8Array(n * 3);
  const t0 = performance.now();
  if (legacy) pl.expose(scene, film, look, pos); else pl.expose(scene, film, look, pic, pos);
  const t1 = performance.now();
  for (let i = 0; i < n * 3; i += 3) pl.lutApply(table, pos[i], pos[i + 1], pos[i + 2], out, i);
  const t2 = performance.now();
  return { out, expose: t1 - t0, lut: t2 - t1 };
}
function compare(name, a, b) {
  let diff = 0, max = 0;
  for (let i = 0; i < a.length; i++) { const d = Math.abs(a[i] - b[i]); if (d) { diff++; if (d > max) max = d; } }
  console.log(`  ${name}: ${diff ? diff + " of " + a.length + " values differ (" + (100 * diff / a.length).toFixed(4) + " %), by at most " + max : "identical"}`);
  return diff;
}
for (const key of ["portra400", "cinestill800t", "velvia50", "hp5", "ektar100"]) {
  const film = films.find(f => f.key === key), base = u8("look_" + key + ".bin");
  const table = P.trimTable(base, zeros, film.mono);
  console.log(key + (film.slide ? " (slide)" : "") + (film.mono ? " (mono)" : "") + ` balance ${film.balance} halation ${film.halation}`);
  compare("untrimmed table = the film's own", table, base);
  const s = develop(P, film, scene, table);
  compare("screen print 720 x 480 vs the camera's", s.out, u8("ref_" + key + "_s.rgb"));
  if (OLD) compare("screen print vs the page as it was", s.out, develop(OLD, film, scene, table, true).out);
  const m = develop(P, film, scene.big, table);
  compare(`Medium print ${BW} x ${BH} vs the camera's`, m.out, u8("ref_" + key + "_m.rgb"));
  console.log(`  time: screen ${(s.expose).toFixed(0)} + ${(s.lut).toFixed(0)} ms; Medium expose ${(m.expose).toFixed(0)} ms, table ${(m.lut).toFixed(0)} ms`);
}
