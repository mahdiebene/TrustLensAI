// Generates the TrustLens toolbar icons (16/48/128) as RGBA PNGs from the
// canonical brand mark used on the website (frontend/public/favicon.svg):
//   - dark rounded tile (#0F0F12)
//   - blue (#3b82f6) shield outline + scanning lens + handle + center dot
// No external deps. Run:  node extension/gen-icons.js
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

// Canonical colors (favicon.svg)
const TILE = [0x0f, 0x0f, 0x12];   // #0F0F12
const BLUE = [0x3b, 0x82, 0xf6];   // #3b82f6

// All geometry below is authored in the 32x32 viewBox of favicon.svg, then
// scaled by k = S/32. Stroke width 1.6 in that space.
const STROKE = 1.6;

// distance from point P to segment AB
function distToSeg(px, py, ax, ay, bx, by) {
  const vx = bx - ax, vy = by - ay;
  const wx = px - ax, wy = py - ay;
  const len2 = vx * vx + vy * vy;
  let t = len2 ? (wx * vx + wy * vy) / len2 : 0;
  t = Math.max(0, Math.min(1, t));
  const cx = ax + t * vx, cy = ay + t * vy;
  return Math.hypot(px - cx, py - cy);
}

// Shield outline path points (matches favicon "M16 5 L25 8.2 V15 C... Z").
// We approximate the curved lower portion with a polyline for stroke hit-test.
function buildShield() {
  const pts = [];
  pts.push([16, 5]);
  pts.push([25, 8.2]);
  pts.push([25, 15]);
  // right curve down to the point at (16, 26.5)
  const steps = 24;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    // quadratic-ish bezier C 25 20.2 21.4 24.2 16 26.5
    const x = bez(25, 25, 21.4, 16, t);
    const y = bez(15, 20.2, 24.2, 26.5, t);
    pts.push([x, y]);
  }
  // left curve back up (mirror) to (7,15)
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const x = bez(16, 10.6, 7, 7, t);
    const y = bez(26.5, 24.2, 20.2, 15, t);
    pts.push([x, y]);
  }
  pts.push([7, 8.2]);
  pts.push([16, 5]);
  return pts;
}
function bez(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
}

const SHIELD = buildShield();

function onShield(x, y, hw) {
  for (let i = 0; i < SHIELD.length - 1; i++) {
    const [ax, ay] = SHIELD[i];
    const [bx, by] = SHIELD[i + 1];
    if (distToSeg(x, y, ax, ay, bx, by) <= hw) return true;
  }
  return false;
}

function onCircle(x, y, cx, cy, r, hw) {
  const d = Math.abs(Math.hypot(x - cx, y - cy) - r);
  return d <= hw;
}

function inDisc(x, y, cx, cy, r) {
  return Math.hypot(x - cx, y - cy) <= r;
}

// rounded-tile coverage (rx=7 in 32 space)
function tileAlpha(x, y) {
  const S = 32, m = 0, r = 7;
  const left = m, top = m, right = S - m, bottom = S - m;
  const cx = x < left + r ? left + r : x > right - r ? right - r : x;
  const cy = y < top + r ? top + r : y > bottom - r ? bottom - r : y;
  const d = Math.hypot(x - cx, y - cy);
  if (d <= r) return 1;
  if (d <= r + 1) return Math.max(0, r + 1 - d);
  return 0;
}

function makePng(S) {
  const k = S / 32;
  const hw = (STROKE / 2);          // half stroke in 32-space
  const aa = 0.6;                    // anti-alias band in 32-space
  const raw = Buffer.alloc((S * 4 + 1) * S);
  let o = 0;
  for (let py = 0; py < S; py++) {
    raw[o++] = 0; // filter: none
    for (let px = 0; px < S; px++) {
      // sample center in 32-space
      const x = (px + 0.5) / k;
      const y = (py + 0.5) / k;

      const tA = tileAlpha(x, y);
      let r = TILE[0], g = TILE[1], b = TILE[2];
      let a = Math.round(tA * 255);

      if (tA > 0.01) {
        // blue elements: shield outline, lens ring, handle, center dot
        const blueHit =
          onShield(x, y, hw + aa) ||
          onCircle(x, y, 14.5, 14, 3.6, hw + aa) ||
          (distToSeg(x, y, 17.2, 16.5, 20.5, 19.8) <= hw + aa) ||
          inDisc(x, y, 14.5, 14, 0.95 + aa * 0.5);
        if (blueHit) {
          // blend blue over tile based on tile coverage
          r = BLUE[0]; g = BLUE[1]; b = BLUE[2];
          a = Math.round(tA * 255);
        }
      }
      raw[o++] = r;
      raw[o++] = g;
      raw[o++] = b;
      raw[o++] = a;
    }
  }

  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(S, 0);
  ihdr.writeUInt32BE(S, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // color type RGBA
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
