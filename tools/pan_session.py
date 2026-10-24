#!/usr/bin/python3
# The pan law: a saw (note 48, filter open) at Pan 0-127, both outputs; level of each against centre.
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/pan'
PANS = (0, 16, 32, 48, 64, 80, 96, 112, 127)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for pan in PANS:
        hw = os.path.join(OUT, 'hw_pan%d.wav' % pan)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(osc1_shape=1, osc1_level=127, cutoff=127, volume=40, pan=pan))
            time.sleep(0.3)
            cap = p2rig.capture(hw, 3.0, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(48, 1.5))
            cap.communicate()
    lv = {}
    for pan in PANS:
        x, r = read(os.path.join(OUT, 'hw_pan%d.wav' % pan))
        on = np.flatnonzero(np.abs(x[:, 0]) + np.abs(x[:, 1]) > 0.02)[0]
        s = x[on + int(0.3 * r):on + int(1.3 * r)]
        lv[pan] = 20 * np.log10(np.sqrt(np.mean(s ** 2, axis=0)) + 1e-9)
    c = lv[64]
    print('pan   left  right  (dB against centre)   sqrt law: left right')
    for pan in PANS:
        p = pan / 127.0
        print('%3d  %6.1f %6.1f        %6.1f %6.1f' % (pan, lv[pan][0] - c[0], lv[pan][1] - c[1],
                                                       10 * np.log10(max(1e-9, 1 - p) / 0.5), 10 * np.log10(max(1e-9, p) / 0.5)))
