// The camera's memory card, in the page: a small in-memory file system and
// the WASI calls the film OS (mfilm.wasm) and mkcr2.wasm make on it.
// Only what wasi-libc's stdio and dirent need.

const E = { OK: 0, BADF: 8, EXIST: 20, INVAL: 28, ISDIR: 31, NOENT: 44, NOTDIR: 54, NOTEMPTY: 55 };
const FT = { CHAR: 2, DIR: 3, FILE: 4 };
const enc = new TextEncoder();
const dec = new TextDecoder();

export class Card {
  constructor() { this.nodes = new Map([['', { dir: true, mtime: Date.now() }]]); this.ino = 1; }
  static norm(p) {
    const out = [];
    for (const s of p.split('/')) {
      if (!s || s === '.') continue;
      if (s === '..') out.pop(); else out.push(s);
    }
    return out.join('/');
  }
  get(p) { return this.nodes.get(Card.norm(p)); }
  parent(p) { const i = p.lastIndexOf('/'); return i < 0 ? '' : p.slice(0, i); }
  mkdirs(p) {
    p = Card.norm(p);
    if (!p || this.nodes.has(p)) return;
    this.mkdirs(this.parent(p));
    this.nodes.set(p, { dir: true, ino: this.ino++, mtime: Date.now() });
  }
  write(p, bytes) {
    p = Card.norm(p);
    this.mkdirs(this.parent(p));
    this.nodes.set(p, { dir: false, ino: this.ino++, data: bytes, size: bytes.length, mtime: Date.now() });
  }
  read(p) { const n = this.get(p); return n && !n.dir ? n.data.subarray(0, n.size) : null; }
  list(p) {
    p = Card.norm(p);
    const pre = p ? p + '/' : '';
    const names = [];
    for (const k of this.nodes.keys())
      if (k && k.startsWith(pre) && !k.slice(pre.length).includes('/')) names.push(k.slice(pre.length));
    return names.sort();
  }
  usedBytes() { let n = 0; for (const v of this.nodes.values()) if (!v.dir) n += v.size; return n; }
}

// One instance's view of the card: its open files and the WASI imports.
export class Wasi {
  constructor(card, { args = [], env = {}, onOut = (s) => console.log(s) } = {}) {
    this.card = card;
    this.args = args;
    this.env = Object.entries(env).map(([k, v]) => `${k}=${v}`);
    this.onOut = onOut;
    this.fds = new Map([
      [0, { tty: true }], [1, { tty: true }], [2, { tty: true }],
      [3, { pre: '/', path: '' }], [4, { pre: '.', path: '' }],
    ]);
    this.nextFd = 5;
    this.line = '';
  }
  bind(memory) { this.memory = memory; }
  get dv() { return new DataView(this.memory.buffer); }
  get u8() { return new Uint8Array(this.memory.buffer); }
  str(ptr, len) { return dec.decode(this.u8.subarray(ptr, ptr + len)); }
  resolve(fd, ptr, len) {
    const d = this.fds.get(fd);
    if (!d || d.path === undefined) return null;
    return Card.norm(d.path + '/' + this.str(ptr, len));
  }
  out(bytes) {
    this.line += dec.decode(bytes);
    let i;
    while ((i = this.line.indexOf('\n')) >= 0) { this.onOut(this.line.slice(0, i)); this.line = this.line.slice(i + 1); }
  }

  imports() {
    const w = this;
    const iov = (iovs, n, fn) => {
      let total = 0;
      for (let i = 0; i < n; i++) {
        const p = w.dv.getUint32(iovs + i * 8, true), l = w.dv.getUint32(iovs + i * 8 + 4, true);
        const done = fn(p, l);
        total += done;
        if (done < l) break;
      }
      return total;
    };
    const filestat = (buf, node) => {
      const dv = w.dv;
      for (let i = 0; i < 64; i += 8) dv.setBigUint64(buf + i, 0n, true);
      dv.setBigUint64(buf + 8, BigInt(node.ino || 0), true);
      dv.setUint8(buf + 16, node.dir ? FT.DIR : FT.FILE);
      dv.setBigUint64(buf + 24, 1n, true);
      dv.setBigUint64(buf + 32, BigInt(node.dir ? 0 : node.size), true);
      const t = BigInt(node.mtime || 0) * 1000000n;
      dv.setBigUint64(buf + 40, t, true); dv.setBigUint64(buf + 48, t, true); dv.setBigUint64(buf + 56, t, true);
    };
    return {
      args_sizes_get(argc, size) {
        w.dv.setUint32(argc, w.args.length, true);
        w.dv.setUint32(size, w.args.reduce((n, a) => n + enc.encode(a).length + 1, 0), true);
        return E.OK;
      },
      args_get(argv, buf) {
        for (const a of w.args) {
          const b = enc.encode(a + '\0');
          w.dv.setUint32(argv, buf, true); argv += 4;
          w.u8.set(b, buf); buf += b.length;
        }
        return E.OK;
      },
      environ_sizes_get(n, size) {
        w.dv.setUint32(n, w.env.length, true);
        w.dv.setUint32(size, w.env.reduce((t, a) => t + enc.encode(a).length + 1, 0), true);
        return E.OK;
      },
      environ_get(envp, buf) {
        for (const a of w.env) {
          const b = enc.encode(a + '\0');
          w.dv.setUint32(envp, buf, true); envp += 4;
          w.u8.set(b, buf); buf += b.length;
        }
        return E.OK;
      },
      proc_exit(code) { throw new WasiExit(code); },

      fd_prestat_get(fd, buf) {
        const d = w.fds.get(fd);
        if (!d || !d.pre) return E.BADF;
        w.dv.setUint8(buf, 0);
        w.dv.setUint32(buf + 4, enc.encode(d.pre).length, true);
        return E.OK;
      },
      fd_prestat_dir_name(fd, ptr, len) {
        const d = w.fds.get(fd);
        if (!d || !d.pre) return E.BADF;
        w.u8.set(enc.encode(d.pre).subarray(0, len), ptr);
        return E.OK;
      },
      fd_fdstat_get(fd, buf) {
        const d = w.fds.get(fd);
        if (!d) return E.BADF;
        const node = d.tty ? null : w.card.get(d.path);
        w.dv.setUint8(buf, d.tty ? FT.CHAR : node && node.dir ? FT.DIR : FT.FILE);
        w.dv.setUint16(buf + 2, d.append ? 1 : 0, true);
        w.dv.setBigUint64(buf + 8, 0xFFFFFFFFFFFFFFFFn, true);
        w.dv.setBigUint64(buf + 16, 0xFFFFFFFFFFFFFFFFn, true);
        return E.OK;
      },
      fd_fdstat_set_flags() { return E.OK; },
      fd_filestat_get(fd, buf) {
        const d = w.fds.get(fd);
        const node = d && !d.tty && w.card.get(d.path);
        if (!node) return E.BADF;
        filestat(buf, node);
        return E.OK;
      },
      path_filestat_get(fd, flags, ptr, len, buf) {
        const p = w.resolve(fd, ptr, len);
        const node = p !== null && w.card.get(p);
        if (!node) return E.NOENT;
        filestat(buf, node);
        return E.OK;
      },
      path_open(dirfd, dirflags, ptr, len, oflags, rb, ri, fdflags, fdOut) {
        const p = w.resolve(dirfd, ptr, len);
        if (p === null) return E.BADF;
        let node = w.card.get(p);
        const CREAT = 1, DIRECTORY = 2, EXCL = 4, TRUNC = 8;
        if (node && (oflags & EXCL) && (oflags & CREAT)) return E.EXIST;
        if (!node) {
          if (!(oflags & CREAT)) return E.NOENT;
          const par = w.card.get(w.card.parent(p));
          if (!par || !par.dir) return E.NOENT;
          w.card.write(p, new Uint8Array(0));
          node = w.card.get(p);
        }
        if ((oflags & DIRECTORY) && !node.dir) return E.NOTDIR;
        if (!node.dir && (oflags & TRUNC)) { node.size = 0; node.mtime = Date.now(); }
        const fd = w.nextFd++;
        w.fds.set(fd, { path: p, pos: 0, append: !!(fdflags & 1) });
        w.dv.setUint32(fdOut, fd, true);
        return E.OK;
      },
      fd_close(fd) { return w.fds.delete(fd) ? E.OK : E.BADF; },
      fd_read(fd, iovs, n, nread) {
        const d = w.fds.get(fd);
        if (!d) return E.BADF;
        if (d.tty) { w.dv.setUint32(nread, 0, true); return E.OK; }
        const node = w.card.get(d.path);
        if (!node || node.dir) return E.ISDIR;
        const total = iov(iovs, n, (p, l) => {
          const k = Math.max(0, Math.min(l, node.size - d.pos));
          w.u8.set(node.data.subarray(d.pos, d.pos + k), p);
          d.pos += k;
          return k;
        });
        w.dv.setUint32(nread, total, true);
        return E.OK;
      },
      fd_write(fd, iovs, n, nwritten) {
        const d = w.fds.get(fd);
        if (!d) return E.BADF;
        if (d.tty) {
          const total = iov(iovs, n, (p, l) => { w.out(w.u8.slice(p, p + l)); return l; });
          w.dv.setUint32(nwritten, total, true);
          return E.OK;
        }
        const node = w.card.get(d.path);
        if (!node || node.dir) return E.ISDIR;
        const total = iov(iovs, n, (p, l) => {
          if (d.append) d.pos = node.size;
          const end = d.pos + l;
          if (end > node.data.length) {
            const grown = new Uint8Array(Math.max(end, node.data.length * 2, 4096));
            grown.set(node.data.subarray(0, node.size));
            node.data = grown;
          }
          node.data.set(w.u8.subarray(p, p + l), d.pos);
          d.pos = end;
          node.size = Math.max(node.size, end);
          return l;
        });
        node.mtime = Date.now();
        w.dv.setUint32(nwritten, total, true);
        return E.OK;
      },
      fd_seek(fd, offset, whence, newOff) {
        const d = w.fds.get(fd);
        if (!d || d.tty) return E.BADF;
        const node = w.card.get(d.path);
        const off = Number(offset);
        const pos = whence === 0 ? off : whence === 1 ? d.pos + off : node.size + off;
        if (pos < 0) return E.INVAL;
        d.pos = pos;
        w.dv.setBigUint64(newOff, BigInt(pos), true);
        return E.OK;
      },
      fd_tell(fd, out) {
        const d = w.fds.get(fd);
        if (!d || d.tty) return E.BADF;
        w.dv.setBigUint64(out, BigInt(d.pos), true);
        return E.OK;
      },
      fd_readdir(fd, buf, len, cookie, used) {
        const d = w.fds.get(fd);
        const node = d && !d.tty && w.card.get(d.path);
        if (!node || !node.dir) return E.NOTDIR;
        const names = ['.', '..', ...w.card.list(d.path)];
        let at = 0;
        for (let i = Number(cookie); i < names.length && at < len; i++) {
          const name = enc.encode(names[i]);
          const child = i < 2 ? node : w.card.get(d.path + '/' + names[i]);
          const ent = new Uint8Array(24 + name.length);
          const dv = new DataView(ent.buffer);
          dv.setBigUint64(0, BigInt(i + 1), true);
          dv.setBigUint64(8, BigInt(child.ino || 0), true);
          dv.setUint32(16, name.length, true);
          dv.setUint8(20, child.dir ? FT.DIR : FT.FILE);
          ent.set(name, 24);
          const k = Math.min(ent.length, len - at);
          w.u8.set(ent.subarray(0, k), buf + at);
          at += k;
        }
        w.dv.setUint32(used, at, true);
        return E.OK;
      },
      path_create_directory(fd, ptr, len) {
        const p = w.resolve(fd, ptr, len);
        if (p === null) return E.BADF;
        if (w.card.get(p)) return E.EXIST;
        if (!w.card.get(w.card.parent(p))) return E.NOENT;
        w.card.mkdirs(p);
        return E.OK;
      },
      path_unlink_file(fd, ptr, len) {
        const p = w.resolve(fd, ptr, len);
        const node = p !== null && w.card.get(p);
        if (!node) return E.NOENT;
        if (node.dir) return E.ISDIR;
        w.card.nodes.delete(p);
        return E.OK;
      },
      path_remove_directory(fd, ptr, len) {
        const p = w.resolve(fd, ptr, len);
        const node = p !== null && w.card.get(p);
        if (!node) return E.NOENT;
        if (!node.dir) return E.NOTDIR;
        if (w.card.list(p).length) return E.NOTEMPTY;
        w.card.nodes.delete(p);
        return E.OK;
      },
      clock_time_get(id, prec, out) { w.dv.setBigUint64(out, BigInt(Date.now()) * 1000000n, true); return E.OK; },
      random_get(buf, len) { crypto.getRandomValues(w.u8.subarray(buf, buf + len)); return E.OK; },
    };
  }
}

export class WasiExit extends Error {
  constructor(code) { super('exit ' + code); this.code = code; }
}
