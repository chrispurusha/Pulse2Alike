#!/usr/bin/python3
# Osc 3 -> DRIVE depth, from the instrument alone. TUBE with a quiet saw changes level steeply with Drive, so a static
# sweep of Drive gives level -> drive; then osc 3 as an 8 Hz square on DRIVE kicks the drive at each edge, and the
# peak level after an edge is read back through the sweep. Note 24: osc 1 four octaves up (note 72), osc 3 two down.
# usage: drive_route_session.py <outdir>
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

RATE = 192000
BASE = dict(osc1_shape=1, osc1_level=30, osc1_semi=112, osc3_shape=0, osc3_semi=40, drive_curve=1, volume=40)


def take(outdir, tag, sound, seconds=1.6):
    p2rig.set_sound(dict(BASE, **sound))
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(24, seconds))
    cap.communicate()
    return path


def envelope(path, ms=2.0):
    x2, r = read(path)
    x = x2[:, 0]
    n = int(r * ms / 1000)
    e = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode='same'))[::n]
    on = np.flatnonzero(e > e.max() * 0.05)[0]
    return 20 * np.log10(e[on + int(300 / ms):on + int(1400 / ms)] + 1e-9)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    drives = (0, 8, 16, 24, 32, 48, 64)
    static = [np.median(envelope(take(outdir, 'static_d%d' % d, dict(drive=d, osc3_level=0)))) for d in drives]
    print('static TUBE, Drive -> level dB:', ' '.join('%d:%.1f' % (d, l) for d, l in zip(drives, static)))
    for lv in (32, 64, 127):
        e = envelope(take(outdir, 'kick_l%d' % lv, dict(drive=0, osc3_routing=3, osc3_level=lv)))
        top, base = np.percentile(e, 99), np.median(e)
        kick = np.interp(top, static, drives)
        print('osc 3 level %3d: base %.1f dB, peak %.1f dB -> drive kick %.1f' % (lv, base, top, kick))


if __name__ == '__main__':
    main()
