#!/usr/bin/python3
# Osc 3's FB shape (the drive's output back into the mixer, at osc 3's level): with a saw (osc 1 level 64, filter
# open, drive off), and alone (no oscillators, cutoff 64); level and harmonics, instrument against engine.
# usage: fb_session.py <outdir>
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

HERE = os.path.dirname(os.path.abspath(__file__))
TONE = open('/private/tmp/claude-501/-Users-chris-Documents-GitHub/637963f3-4fcf-4a90-acaa-d2b119322a34/scratchpad/caltone.txt').read().split()
F0 = 130.8128


def measure(path, gain=1.0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > 1e-4)
    if len(on) == 0:
        return -150.0, [], 0.0
    s = x[on[0] + int(0.3 * r):on[0] + int(1.0 * r)]
    s = s - s.mean()
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    a = np.array([abs(np.sum(s * w * np.exp(-2j * np.pi * F0 * k * t))) for k in range(1, 7)])
    X = np.abs(np.fft.rfft(s * w))
    f = np.fft.rfftfreq(len(s), 1 / r)
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12), 20 * np.log10(a / a.max() + 1e-9), f[np.argmax(X[1:]) + 1]


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for name, sound, over in (('saw', dict(osc1_level=64), ['osc1level=64']),
                              ('alone', dict(osc1_level=0, cutoff=64), ['osc1level=0', 'cutoff=64'])):
        print(name)
        for lv in (0, 32, 64, 96, 127):
            hw = os.path.join(outdir, 'hw_%s_%d.wav' % (name, lv))
            if not os.path.exists(hw):
                p2rig.set_sound(dict(volume=40, osc3_shape=4, osc3_level=lv, **sound))
                time.sleep(0.3)
                cap = p2rig.capture(hw, 2.8, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(48, 1.2))
                cap.communicate()
            en = os.path.join(outdir, 'p2_%s_%d.wav' % (name, lv))
            subprocess.run([os.path.join(HERE, 'p2render'), '-', '48', '1.2', '0.1', en, '192000', *TONE, 'osc3shape=4',
                            'osc3level=%d' % lv, *over], check=True, capture_output=True)
            lh, ah, fh = measure(hw)
            le, ae, fe = measure(en, 10.0)
            print('  FB %3d: hw %6.1f dB peak %6.0f Hz %s | eng %6.1f dB peak %6.0f Hz %s' % (
                lv, lh, fh, ' '.join('%.0f' % v for v in ah), le, fe, ' '.join('%.0f' % v for v in ae)))


if __name__ == '__main__':
    main()
