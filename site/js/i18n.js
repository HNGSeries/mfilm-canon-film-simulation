// English and Thai: the page's text (data-i18n) and the camera's status line.

const STR = {
  en: {
    'nav.films': 'Films', 'nav.cameras': 'Cameras', 'nav.download': 'Download',
    'hero.title': 'Your Canon,<br>shot like film.',
    'hero.lede': 'This is M-Film running on an EOS M, in your browser: the same menus, drawn by the same code as on the camera. Load a roll, shoot it, then develop it.',
    'picker.more': 'more soon',
    'picker.label': 'Camera', 'picker.soon': 'Coming to the browser',
    'get.t': 'Put it on your camera',
    'get.d': 'One zip for your camera: unzip it onto the card, and the camera starts with M-Film. Pay what you want for it, from nothing at all.',
    'dl.t': 'Download M-Film', 'dl.camera': 'Your camera', 'dl.price': 'Name your price',
    'dl.free': '$0 is fine: M-Film is free and open source. Whatever you give keeps it going.',
    'dl.pay': (v) => `Pay $${v} and download`, 'dl.freeGo': 'Download free', 'dl.wait': 'Opening Stripe…',
    'dl.secure': 'Payment by Stripe. The download starts when you come back.',
    'dl.all': 'All files and release notes',
    'dl.err': (url) => `Stripe can't be reached right now. <a href="${url}">Download free instead</a>, or try again in a minute.`,
    'dl.issues': 'known problems', 'dl.testing': 'needs testers',
    'dl.note.issues': 'Works with a known problem on this camera: the README says which.',
    'dl.note.testing': 'Not tried on this camera yet: be the first, and tell us how it goes.',
    'dl.thanks.t': 'Thank you!', 'dl.thanks.d': 'Your download has started. If it hasn\'t, use the button.',
    'dl.again': 'Download again',
    'dl.next': 'Unzip it onto the card and turn the camera on. The README in the zip has the rest.',
    'cam.loading': 'Loading the film OS…', 'cam.dial': 'dial',
    'g.load.t': 'Load a roll', 'g.load.d': 'Turn the dial (or ← →) along the shelf, SET to load. 12 frames is quickest.',
    'g.shoot.t': 'Shoot the roll', 'g.shoot.d': 'Press the shutter on top (or Space). No picture comes up: that\'s the point.',
    'g.develop.t': 'Develop it', 'g.develop.d': 'When the roll is finished the camera asks. Develop it, and watch the darkroom work.',
    'g.prints.t': 'See the prints', 'g.prints.d': 'PLAY shows the contact sheet and every print.',
    'g.keys': 'Keyboard',
    'k.shutter': 'shutter (hold: half-press)', 'k.dial': 'dial presses', 'k.wheel': 'turn the dial', 'k.home': 'delete: M-Film home',
    'cta.free': 'Download for your Canon',
    'films.t': '72 films, on four shelves',
    'films.d': 'Colour negative, slide, black and white, and cinema film. Each has its own colour, grain, halation and softness.',
    'cams.t': 'For Canon cameras that run Magic Lantern',
    'cams.d': 'Works on the EOS M, 6D, 60D, 50D, 500D, 550D, 100D and 650D; the 700D, 70D, 5D Mark III, 5D Mark II and 1100D are being tested. The camera side is free and open source (GPL-2.0).',
    'cams.link': 'Every camera and how far it got →',
    'dr.t': 'Develop on your computer: Darkrooms',
    'dr.d': 'The camera develops its rolls by itself, slowly. Darkrooms does it on your computer, fast: plug the camera in, and every roll is there.',
    'p.free': 'Free', 'p.free.d': 'one roll a day, up to 36 frames', 'p.month': 'a month', 'p.once': 'once, for good',
    'foot.ml': 'Built on <a href="https://www.magiclantern.fm/">Magic Lantern</a>. Not affiliated with Canon.',
    'st.boot': 'Starting…',
    'st.menu': 'M-Film is open: pick a film',
    'st.open': 'M-Film is open: half-press the shutter to go back',
    'st.noroll': 'No film in the camera: load a roll first',
    'st.roll': (n, of) => `LiveView · frame ${n} of ${of}`,
    'st.wind': 'Press SET to wind on',
    'st.finished': 'Roll finished: press SET to develop it',
    'st.developing': 'Developing in the camera…',
    'st.developed': 'Developed: PLAY shows the prints',
    'st.crash': 'The camera stopped. Reload the page to start again.',
  },
  th: {
    'nav.films': 'ฟิล์ม', 'nav.cameras': 'กล้อง', 'nav.download': 'ดาวน์โหลด',
    'hero.title': 'เปลี่ยน Canon ของคุณ<br>ให้ถ่ายเหมือนกล้องฟิล์ม',
    'hero.lede': 'นี่คือ M-Film ที่รันบน EOS M ในเบราว์เซอร์ของคุณ เมนูเดียวกัน วาดด้วยโค้ดชุดเดียวกับในกล้องจริง ลองใส่ฟิล์ม ถ่ายให้หมดม้วน แล้วล้างฟิล์มดู',
    'picker.more': 'รุ่นอื่นเร็วๆ นี้',
    'picker.label': 'กล้อง', 'picker.soon': 'เร็วๆ นี้บนเว็บ',
    'get.t': 'ลงในกล้องของคุณ',
    'get.d': 'zip ไฟล์เดียวต่อรุ่น แตกไฟล์ลงการ์ด เปิดกล้องก็เข้า M-Film เลย จ่ายเท่าไหร่ก็ได้ตามใจ ตั้งแต่ $0',
    'dl.t': 'ดาวน์โหลด M-Film', 'dl.camera': 'กล้องของคุณ', 'dl.price': 'ตั้งราคาเอง',
    'dl.free': '$0 ก็ได้ M-Film ฟรีและเปิดซอร์ส ทุกดอลลาร์ที่ให้ช่วยให้พัฒนาต่อได้',
    'dl.pay': (v) => `จ่าย $${v} แล้วดาวน์โหลด`, 'dl.freeGo': 'ดาวน์โหลดฟรี', 'dl.wait': 'กำลังเปิด Stripe…',
    'dl.secure': 'ชำระเงินผ่าน Stripe จ่ายเสร็จกลับมาหน้านี้แล้วดาวน์โหลดจะเริ่มเอง',
    'dl.all': 'ไฟล์ทั้งหมดและบันทึกการอัปเดต',
    'dl.err': (url) => `ติดต่อ Stripe ไม่ได้ตอนนี้ <a href="${url}">ดาวน์โหลดฟรีไปก่อน</a> หรือลองใหม่อีกสักครู่`,
    'dl.issues': 'มีปัญหาที่รู้แล้ว', 'dl.testing': 'รอคนทดสอบ',
    'dl.note.issues': 'ใช้ได้แต่มีปัญหาที่รู้แล้วในรุ่นนี้ ดูรายละเอียดใน README',
    'dl.note.testing': 'ยังไม่มีใครลองกับรุ่นนี้ ลองเป็นคนแรกแล้วบอกเราด้วย',
    'dl.thanks.t': 'ขอบคุณครับ!', 'dl.thanks.d': 'ดาวน์โหลดเริ่มแล้ว ถ้ายังไม่เริ่ม กดปุ่มด้านล่าง',
    'dl.again': 'ดาวน์โหลดอีกครั้ง',
    'dl.next': 'แตกไฟล์ลงการ์ดแล้วเปิดกล้อง รายละเอียดที่เหลืออยู่ใน README ใน zip',
    'cam.loading': 'กำลังโหลด film OS…', 'cam.dial': 'แป้นหมุน',
    'g.load.t': 'ใส่ฟิล์ม', 'g.load.d': 'หมุนแป้น (หรือ ← →) ไปตามชั้นวาง กด SET เพื่อใส่ม้วน เลือก 12 รูปจะเร็วสุด',
    'g.shoot.t': 'ถ่ายให้หมดม้วน', 'g.shoot.d': 'กดชัตเตอร์ด้านบน (หรือ Space) ถ่ายแล้วไม่มีภาพขึ้นจอ เหมือนกล้องฟิล์ม',
    'g.develop.t': 'ล้างฟิล์ม', 'g.develop.d': 'ถ่ายครบม้วนแล้วกล้องจะถาม เลือกล้างฟิล์ม แล้วดูห้องมืดทำงาน',
    'g.prints.t': 'ดูรูปที่ล้างแล้ว', 'g.prints.d': 'กด PLAY เพื่อดู contact sheet และรูปทีละใบ',
    'g.keys': 'ปุ่มบนคีย์บอร์ด',
    'k.shutter': 'ชัตเตอร์ (กดค้าง: แตะครึ่งทาง)', 'k.dial': 'กดขอบแป้น', 'k.wheel': 'หมุนแป้น', 'k.home': 'ปุ่มลบ: หน้า Home ของ M-Film',
    'cta.free': 'ดาวน์โหลดสำหรับกล้อง Canon ของคุณ',
    'films.t': 'ฟิล์ม 72 แบบ บนชั้นวาง 4 ชั้น',
    'films.d': 'ฟิล์มสีเนกาทีฟ สไลด์ ขาวดำ และฟิล์มภาพยนตร์ แต่ละม้วนมีสี เกรน halation และความนุ่มของตัวเอง',
    'cams.t': 'สำหรับกล้อง Canon ที่ลง Magic Lantern ได้',
    'cams.d': 'ใช้ได้บน EOS M, 6D, 60D, 50D, 500D, 550D, 100D และ 650D ส่วน 700D, 70D, 5D Mark III, 5D Mark II และ 1100D กำลังทดสอบ ส่วนในกล้องใช้ฟรีและเปิดซอร์ส (GPL-2.0)',
    'cams.link': 'ดูทุกรุ่นและสถานะ →',
    'dr.t': 'ล้างบนคอม: Darkrooms',
    'dr.d': 'กล้องล้างฟิล์มเองได้แต่ช้า Darkrooms ล้างบนคอมได้เร็ว เสียบสายกล้องแล้วทุกม้วนก็ขึ้นมาเลย',
    'p.free': 'ฟรี', 'p.free.d': 'วันละ 1 ม้วน ไม่เกิน 36 รูป', 'p.month': 'ต่อเดือน', 'p.once': 'จ่ายครั้งเดียว ใช้ได้ตลอด',
    'foot.ml': 'ทำงานบน <a href="https://www.magiclantern.fm/">Magic Lantern</a> ไม่เกี่ยวข้องกับ Canon',
    'st.boot': 'กำลังเปิดกล้อง…',
    'st.menu': 'M-Film เปิดอยู่: เลือกฟิล์ม',
    'st.open': 'M-Film เปิดอยู่: แตะชัตเตอร์ครึ่งทางเพื่อกลับไปถ่าย',
    'st.noroll': 'ยังไม่มีฟิล์มในกล้อง ใส่ม้วนก่อน',
    'st.roll': (n, of) => `LiveView · รูปที่ ${n} จาก ${of}`,
    'st.wind': 'กด SET เพื่อขึ้นฟิล์ม',
    'st.finished': 'ฟิล์มหมดม้วนแล้ว กด SET เพื่อล้าง',
    'st.developing': 'กำลังล้างฟิล์มในกล้อง…',
    'st.developed': 'ล้างเสร็จแล้ว กด PLAY เพื่อดูรูป',
    'st.crash': 'กล้องหยุดทำงาน รีโหลดหน้าเพื่อเริ่มใหม่',
  },
};

let lang = (() => {
  try { const s = localStorage.getItem('mfilm.lang'); if (s) return s; } catch {}
  return /^th\b/i.test(navigator.language) ? 'th' : 'en';
})();

export function T(id, ...args) {
  const v = STR[lang][id] ?? STR.en[id] ?? id;
  return typeof v === 'function' ? v(...args) : v;
}

export function applyLang() {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll('[data-i18n]')) {
    const v = STR[lang][el.dataset.i18n];
    if (typeof v === 'string') el.innerHTML = v;
  }
  for (const el of document.querySelectorAll('[data-i18n-label]')) el.label = T(el.dataset.i18nLabel);
  const b = document.querySelector('.lang');
  if (b) b.textContent = lang === 'th' ? 'EN' : 'TH';
}

export function toggleLang() {
  lang = lang === 'th' ? 'en' : 'th';
  try { localStorage.setItem('mfilm.lang', lang); } catch {}
  applyLang();
  document.dispatchEvent(new Event('mfilm:lang'));
}
