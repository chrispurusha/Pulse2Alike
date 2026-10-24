#!/usr/bin/python3
# The absolute side patch_validate.py leaves out: per patch and window, the engine's level against the instrument's
# (median third-octave difference, the render gain of 10 restored) and the spectral rms after it, in dB.
# usage: patch_levels.py <folder with hw_lfo0_NNN.wav and p2_lfo0_NNN.wav> [first last]
import os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_validate import WINDOWS, bands, onset, read


def levels(folder, n):
    xh, rh = read(os.path.join(folder, 'hw_lfo0_%03d.wav' % n))
    xp, rp = read(os.path.join(folder, 'p2_lfo0_%03d.wav' % n))
    xp = xp * 10.0
    sh, sp = onset(xh, rh), onset(xp, rp)
    out = []
    for _, a, b in WINDOWS:
        bh = bands(xh[sh + int(a * rh):sh + int(b * rh)], rh)
        bp = bands(xp[sp + int(a * rp):sp + int(b * rp)], rp)
        ok = (bh > bh.max() - 40) & np.isfinite(bp)
        d = (bp - bh)[ok]
        out.append((np.median(d), np.sqrt(np.mean((d - np.median(d)) ** 2))))
    return out


if __name__ == '__main__':
    first, last = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1, 15)
    for n in range(first, last + 1):
        print('%03d ' % n + ' | '.join('%s %+5.1f dB (%.1f)' % (w[0], o, r) for w, (o, r) in zip(WINDOWS, levels(sys.argv[1], n))))
