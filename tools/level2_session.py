#!/usr/bin/python3
# LEVEL2 measured for a law: osc 2 a saw at +36 (2093 Hz at note 60), osc 3 on LEVEL2 at -48 (16.35 Hz) as SAW and SQR
# at Levels 15-127, osc 2's own Level 101 (64 and 127 for some), filter open, osc 1 and noise off, sync off.
# osc 2's envelope folded on osc 3's period; the engine rendered the same way.  usage: level2_session.py [analyse]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/level2_law'
NOTE, F2, F3 = 60, 2093.0, 261.6256 / 16
LEVELS = (0, 15, 30, 45, 58, 75, 90, 110, 127)
CASES = [('saw', 1, lv, 101) for lv in LEVELS] + [('sqr', 0, lv, 101) for lv in LEVELS] + \
        [('saw', 1, lv, l2) for l2 in (64, 127) for lv in (0, 30, 58, 127)] + \
        [('saw', 1, lv, l2) for l2 in (40, 80) for lv in (0, 30, 58, 90)] + [('saw', 1, 90, 64)]


def tag(shape, lv, l2):
    return '%s_l%d_o2%d' % (shape, lv, l2)


def capture():
    os.makedirs(OUT, exist_ok=True)
    for shape, s3, lv, l2 in CASES:
        hw = os.path.join(OUT, 'hw_%s.wav' % tag(shape, lv, l2))
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(osc1_level=0, osc2_shape=1, osc2_level=l2, osc2_semi=64 + 36, osc3_shape=s3, osc3_routing=1,
                             osc3_semi=64 - 48, osc3_level=lv, osc3_sync=0, cutoff=127, volume=40))
        time.sleep(0.3)
        cap = p2rig.capture(hw, 2.6, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, 1.6))
        cap.communicate()


def render(shape, s3, lv, l2, out, extra=()):
    subprocess.run(['./p2render', '-', str(NOTE), '1.6', '0.2', out, '192000', *sq.ENGINE_BASE, 'osc1level=0', 'osc2shape=1',
                    'osc2level=%d' % l2, 'osc2semitone=36', 'osc3shape=%d' % s3, 'osc3routing=1', 'osc3semitone=-48',
                    'osc3level=%d' % lv, 'osc3synctoosc2=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40', *extra],
                   check=True, capture_output=True)


def fold(path, gain, bins=128):
    """osc 2's envelope (one-cycle RMS) folded on osc 3's period, aligned on osc 3's biggest step (its reset or edge)."""
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    w = int(round(r / F2))
    env = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same'))
    on = np.flatnonzero(env > env.max() * 0.1)[0]
    s = env[on + int(0.3 * r):on + int(1.5 * r)]
    period = r / F3
    n = int(len(s) / period) - 1
    cyc = np.array([np.interp(np.arange(bins) * period / bins + k * period, np.arange(len(s)), s) for k in range(n)])
    m = np.mean(cyc, axis=0)
    j = np.argmax(np.abs(np.diff(np.log(m + 1e-9), append=np.log(m[0] + 1e-9)))) + 1
    return np.roll(m, -j)


if __name__ == '__main__':
    if 'analyse' not in sys.argv:
        capture()
    for shape, s3, lv, l2 in CASES:
        if lv == 0:
            continue
        h = fold(os.path.join(OUT, 'hw_%s.wav' % tag(shape, lv, l2)), 1.0)
        h0 = np.mean(fold(os.path.join(OUT, 'hw_%s.wav' % tag(shape, 0, l2)), 1.0))
        print('%-16s mean %+5.1f dB  log fold: %s' % (tag(shape, lv, l2), 20 * np.log10(np.mean(h) / h0),
                                                   ' '.join('%+5.2f' % v for v in np.log(h / h0)[::8])))
