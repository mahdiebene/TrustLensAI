// One-off helper to generate solid-blue "T" PNG icons (16/48/128) for the
// extension without any external dependencies. Writes minimal valid PNGs.
// Run: node extension/gen-icons.js
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
  }
  return ~c >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

// Draw a flat blue square with a white "T" glyph.
function makePng(size) {
  const blue = [59, 130, 246];
  const white = [255, 255, 255];
  const px = (x, y) => {
    // T glyph: top bar + vertical stem, scaled to size.
    const barTop = size * 0.22;
    const barBottom = size * 0.36;
    const barLeft = size * 0.22;
    const barRight = size * 0.78;
    const stemLeft = size * 0.43;
    const stemRight = size * 0.57;
    const stemBottom = size * 0.78;
    const inTopBar = y >= barTop && y < barBottom && x >= barLeft && x < barRight;
    const inStem = y >= barBottom && y < stemBottom && x >= stemLeft && x < stemRight;
    return inTopBar || inStem ? white : blue;
  };

  const raw = Buffer.alloc((size * 3 + 1) * size);
  let o = 0;
  for (let y = 0; y < size; y++) {
    raw[o++] = 0; // filter type none
    for (let x = 0; x < size; x++) {
      const [r, g, b] = px(x, y);
      raw[o++] = r;
      raw[o++] = g;
      raw[o++] = b;
    }
  }

  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 2; // color type RGB
  const idat = zlib.deflateSync(raw);
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', idat),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

const dir = path.join(__dirname, 'icons');
fs.mkdirSync(dir, { recursive: true });
[16, 48, 128].forEach((s) => {
  fs.writeFileSync(path.join(dir, `icon${s}.png`), makePng(s));
  console.log(`wrote icon${s}.png`);
});
