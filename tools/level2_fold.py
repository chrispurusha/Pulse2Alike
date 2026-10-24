#!/usr/bin/python3
# LEVEL2 by osc 3's Level: osc 2's envelope (523 Hz) folded on osc 3's period (32.7 Hz), the instrument's 10-23 takes
# (192k/level2/hw_l*: P006 with osc 1 and noise off, filter open, sync off, osc 2 +12, osc 3 -36, note 60) against the
# engine as built; each relative to its own osc 3 at 0. Prints the fold in 16 steps and its mean.
import os, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read

CAP = '/Volumes/ext-ssd/Captures/Pulse2/192k/level2/'
SYX = '/Volumes/ext-ssd/Captures/Pulse2/192k/patches/fixedlfo_006.syx'
LEVELS = (0, 15, 30, 58, 90, 127)
F3 = 261.6256 / 8


def fold(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    env = np.sqrt(np.convolve(x ** 2, np.ones(int(r / 523.25)) / int(r / 523.25), 'same'))
    on = np.flatnonzero(env > env.max() * 0.1)[0]
    s = env[on + int(0.3 * r):on + int(1.3 * r)]
    period = r / F3
    n = int(len(s) / period) - 1
    cyc = np.array([np.interp(np.arange(64) * period / 64 + k * period, np.arange(len(s)), s) for k in range(n)])
    ref = cyc[0]
    al = [np.roll(c, -int(np.argmax([np.dot(ref, np.roll(c, -j)) for j in range(64)]))) for c in cyc]
    return np.mean(al, axis=0)


def render(level, out, extra=()):
    subprocess.run(['./p2render', SYX, '60', '1.6', '0.2', out, '192000', 'osc1level=0', 'noiselevel=0', 'cutoff=127',
                    'filterenvamount=64', 'resonance=0', 'osc3synctoosc2=0', 'osc2semitone=12', 'osc3semitone=-36',
                    'osc3level=%d' % level, *extra], check=True, capture_output=True)


if __name__ == '__main__':
    d = os.environ.get('TMPDIR', '/tmp')
    h0 = np.mean(fold(CAP + 'hw_l0.wav', 1.0))
    render(0, d + '/l2_0.wav')
    e0 = np.mean(fold(d + '/l2_0.wav', 10.0))
    for lv in LEVELS[1:]:
        h = fold(CAP + 'hw_l%d.wav' % lv, 1.0) / h0
        render(lv, d + '/l2.wav')
        e = fold(d + '/l2.wav', 10.0) / e0
        hs, es = np.sort(h)[::-1], np.sort(e)[::-1]           # sorted, so the free phases do not matter
        print('level %3d  mean: instrument %+.1f dB, engine %+.1f | peak %.2f / %.2f | floor %.2f / %.2f' % (
            lv, 20 * np.log10(np.mean(h)), 20 * np.log10(np.mean(e)), hs[0], es[0], hs[-1], es[-1]))
        print('   instrument sorted:', ' '.join('%.2f' % v for v in hs[::4]))
        print('   engine     sorted:', ' '.join('%.2f' % v for v in es[::4]))
