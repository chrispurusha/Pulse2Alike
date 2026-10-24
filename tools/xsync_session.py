#!/usr/bin/python3
# X3-PWM with sync on: osc 2 (width 64) above osc 3 by 7 and 19 semitones, against plain PWM synced the same way.
# Folds one of osc 3's cycles (note 48) from the instrument's take and the engine's render.  usage: xsync_session.py
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/xpwm'
NOTE, HOLD = 48, 2.0
CASES = {'sync_x3_s7': (3, 7), 'sync_x3_s19': (3, 19), 'sync_pwm_s7': (0, 7), 'sync_pwm_s19': (0, 19), 'sync_saw_s7': (1, 7), 'sync_saw_s19': (1, 19), 'sync_saw_s12': (1, 12)}


def fold(path, gain, f0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.5 * r):on + int(1.5 * r)]
    period = r / f0
    n = int(len(s) / period) - 1
    cyc = np.array([np.interp(np.arange(64) * period / 64 + k * period, np.arange(len(s)), s) for k in range(n)])
    return cyc


if __name__ == '__main__':
    for name, (shape, semi) in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(osc1_level=0, osc2_level=127, osc2_shape=shape, osc2_pw=64, osc2_semi=64 + semi,
                                 osc3_level=0, osc3_shape=0, osc3_sync=1, noise=0, cutoff=127, resonance=0, volume=40))
            time.sleep(0.3)
            cap = p2rig.capture(hw, HOLD + 1.5, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(NOTE, HOLD))
            cap.communicate()
        p2 = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'p2_%s.wav' % name)
        subprocess.run(['./p2render', '-', str(NOTE), str(HOLD), '0.3', p2, '192000', *sq.ENGINE_BASE, 'osc1level=0', 'osc2level=127',
                        'osc2shape=%d' % shape, 'osc2pulsewidth=64', 'osc2semitone=%d' % semi, 'osc3level=0', 'osc3shape=0',
                        'osc3synctoosc2=1', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40'], check=True, capture_output=True)
        f0 = 130.8128
        for side, path, g in (('hw', hw, 1.0), ('p2', p2, 10.0)):
            c = fold(path, g, f0)
            # align each cycle to the first by cross-correlation, so the shape is read whatever the free phase
            ref = c[0]
            al = [np.roll(k, -np.argmax([np.dot(ref, np.roll(k, -j)) for j in range(64)])) for k in c]
            m = np.mean(al, axis=0)
            spread = np.mean(np.std(al, axis=0))
            print('%-14s %s spread %.3f |%s|' % (name, side, spread, ''.join(' .:-=+*#%@'[min(9, int((v - m.min()) / (np.ptp(m) + 1e-9) * 9.99))] for v in m)))
