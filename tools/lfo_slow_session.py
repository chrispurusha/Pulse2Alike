#!/usr/bin/python3
# LFO 1's rate at the slow end of Speed (fast shapes): TRI on osc 1's pitch (mod 1, amount 80), speeds 0/4/9/14,
# the pitch tracked from zero crossings and the LFO period read by autocorrelation; against the engine's law.
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/lfo_slow'
SPEEDS = (0, 4, 9, 14)
HOLD = 14.0


def lfo_period(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on:on + int(HOLD * r)]
    z = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0))
    t = z[1:] / r
    f = r / np.diff(z)
    grid = np.arange(0.2, t[-1], 0.01)
    p = np.interp(grid, t, f)
    p = p - p.mean()
    ac = np.correlate(p, p, 'full')[len(p) - 1:]
    lag = np.argmax(ac[100:]) + 100           # skip the first second
    return lag * 0.01


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    for sp in SPEEDS:
        hw = os.path.join(OUT, 'hw_s%d.wav' % sp)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(osc1_shape=1, osc1_level=127, cutoff=127, volume=40))
            p2rig.send(p2rig.hexmsg(ch, p2rig.CC_LFO1_SPEED, sp), p2rig.hexmsg(ch, p2rig.CC_LFO1_SHAPE, 1),
                       p2rig.hexmsg(ch, p2rig.MOD_SOURCES[0], 1), p2rig.hexmsg(ch, p2rig.MOD_AMOUNTS[0], 80),
                       p2rig.hexmsg(ch, 110, 1))       # mod 1 target: OSC1 PITCH
            time.sleep(0.3)
            cap = p2rig.capture(hw, HOLD + 1.5, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(60, HOLD))
            cap.communicate()
        law = 1.0 / (6.897 * 2 ** ((sp - 64) / 12))
        print('speed %2d: instrument %.2f s   engine law %.2f s' % (sp, lfo_period(hw), law))
