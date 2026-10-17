#!/usr/bin/python3
# The envelope loops (amp envelope): OFF, A-D and D-D with Sustain at three settings, a 4 s hold, the output's
# envelope in dB every 50 ms. usage: loop_session.py <outdir>
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from env_capture import envelope, NOTE, RATE

CASES = [(0, 64), (1, 64), (2, 32), (2, 64), (2, 96)]     # (loop, sustain)
ENV = dict(enva_a=40, enva_d=50, enva_r=40)
HOLD = 4.0


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for loop, sus in CASES:
        p2rig.set_sound(dict(volume=40, enva_loop=loop, enva_s=sus, **ENV))
        time.sleep(0.3)
        path = os.path.join(outdir, 'loop%d_s%d.wav' % (loop, sus))
        cap = p2rig.capture(path, 1.0 + HOLD + 1.5, RATE)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()
        e, fs = envelope(path)
        on = np.flatnonzero(e > e.max() * 1e-3)[0]
        db = 20 * np.log10(e / e.max() + 1e-9)
        print('loop %d sustain %3d: %s' % (loop, sus, ' '.join('%.0f' % db[on + int(t * fs)] for t in np.arange(0, HOLD + 0.6, 0.05) if on + int(t * fs) < len(db))))


if __name__ == '__main__':
    main()
