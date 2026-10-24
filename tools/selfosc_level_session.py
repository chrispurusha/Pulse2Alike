#!/usr/bin/python3
# The self-oscillation's LEVEL and harmonics (its frequency is the cutoff law, filtercheck): no input, resonance 100
# and 127, cutoff 40/64/88, the instrument and the engine (given a 2 s lead-in, as the instrument's oscillates behind
# the closed VCA all along - findings 2026-10-23).  usage: selfosc_level_session.py [analyse]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/selfosc_level'
NOTE, HOLD = 48, 3.0
CASES = [(c, r) for r in (127, 100) for c in (40, 64, 88)]


def capture():
    os.makedirs(OUT, exist_ok=True)
    for cutoff, res in CASES:
        hw = os.path.join(OUT, 'hw_c%d_r%d.wav' % (cutoff, res))
        p2rig.set_sound(dict(osc1_level=0, noise=0, cutoff=cutoff, resonance=res, volume=40))
        time.sleep(1.0)
        cap = p2rig.capture(hw, HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()


def render(path, cutoff, res, env=None):
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', '%d:2.0:%.1f' % (NOTE, HOLD),
                    str(2.0 + HOLD), '0.3', path, '192000', *sq.ENGINE_BASE, 'osc1level=0', 'noiselevel=0',
                    'cutoff=%d' % cutoff, 'resonance=%d' % res, 'volume=40'], check=True, capture_output=True, env=env)


def measure(path, lead=0.0):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    if lead > 0.0:
        on = int((0.1 + lead) * r)
    else:
        on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(1.0 * r):on + int(2.5 * r)]
    s = s - s.mean()
    w = np.hanning(len(s))
    X = np.abs(np.fft.rfft(s * w)) * 2 / w.sum()
    f = np.fft.rfftfreq(len(s), 1 / r)
    k = np.argmax(X * (f > 30))
    f0 = f[k]
    h = [20 * np.log10(X[np.argmin(abs(f - f0 * n))] + 1e-12) for n in (1, 2, 3, 5)]
    return f0, 20 * np.log10(np.sqrt(np.mean(s ** 2))), h


if __name__ == '__main__':
    if 'analyse' not in sys.argv:
        capture()
    for cutoff, res in CASES:
        render(os.path.join(OUT, 'p2_c%d_r%d.wav' % (cutoff, res)), cutoff, res)
        fh, lh, hh = measure(os.path.join(OUT, 'hw_c%d_r%d.wav' % (cutoff, res)))
        fp, lp, hp = measure(os.path.join(OUT, 'p2_c%d_r%d.wav' % (cutoff, res)), 2.0)
        print('c%d r%d  hw %7.1f Hz %6.1f dBFS H2/H3/H5 %s | p2 %7.1f Hz %6.1f dBFS H2/H3/H5 %s' %
              (cutoff, res, fh, lh, ' '.join('%5.1f' % (v - hh[0]) for v in hh[1:]), fp, lp, ' '.join('%5.1f' % (v - hp[0]) for v in hp[1:])))
