#!/usr/bin/python3
# Waveforms to a PNG with numpy alone (no plotting library on this machine): each trace drawn column by column as
# the span of its samples, in its own colour, over a zero line.
# usage: plotwave.py <out.png> <start_s> <length_s> <file.wav>[:gain][:channel] ...   (up to four traces, stacked)
import os, struct, sys, zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read

COLOURS = [(220, 60, 50), (40, 110, 220), (40, 160, 70), (200, 140, 20)]
W, H = 1400, 300


def png(path, img):
    raw = b''.join(b'\x00' + img[y].tobytes() for y in range(img.shape[0]))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    hdr = struct.pack('>IIBBBBB', img.shape[1], img.shape[0], 8, 2, 0, 0, 0)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', hdr) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def trace(img, y0, x, colour, scale):
    n = len(x)
    for c in range(W):
        seg = x[int(c * n / W):max(int((c + 1) * n / W), int(c * n / W) + 1)]
        lo, hi = seg.min(), seg.max()
        a = int(y0 + H / 2 - hi * scale * (H / 2 - 4))
        b = int(y0 + H / 2 - lo * scale * (H / 2 - 4))
        img[max(y0, min(a, b)):min(y0 + H, max(a, b) + 1), c] = colour


def main():
    out, start, length = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    specs = sys.argv[4:]
    img = np.full((H * len(specs), W, 3), 255, np.uint8)
    for i, spec in enumerate(specs):
        parts = spec.split(':')
        x2, r = read(parts[0])
        gain = float(parts[1]) if len(parts) > 1 and parts[1] else 1.0
        ch = int(parts[2]) if len(parts) > 2 else 0
        x = (x2[:, ch] if x2.ndim > 1 else x2) * gain
        x = x[int(start * r):int((start + length) * r)]
        y0 = i * H
        img[y0 + H // 2, :] = (180, 180, 180)
        img[y0, :] = (120, 120, 120)
        trace(img, y0, x, COLOURS[i % 4], 1.0 / max(np.abs(x).max(), 1e-9))
    png(out, img)


if __name__ == '__main__':
    main()
