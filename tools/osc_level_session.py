#!/usr/bin/python3
# Each oscillator's level law: osc 1, osc 2 and osc 3 alone (saw and pulse; osc 3 SAW and SQR), filter open, note 48,
# Levels 20-127, on the instrument and the engine; the level, engine minus instrument.
# usage: osc_level_session.py
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/osc_levels'
LEVELS = (20, 40, 64, 90, 127)
# (name, rig settings, renderer settings) at a Level L
OSCS = (('osc1 saw', lambda L: dict(osc1_shape=1, osc1_level=L), lambda L: ['osc1shape=1', 'osc1level=%d' % L]),
        ('osc1 pwm', lambda L: dict(osc1_shape=0, osc1_pw=64, osc1_level=L), lambda L: ['osc1shape=0', 'osc1pulsewidth=64', 'osc1level=%d' % L]),
        ('osc2 saw', lambda L: dict(osc1_level=0, osc2_shape=1, osc2_level=L), lambda L: ['osc1level=0', 'osc2shape=1', 'osc2level=%d' % L]),
        ('osc2 pwm', lambda L: dict(osc1_level=0, osc2_shape=0, osc2_pw=64, osc2_level=L), lambda L: ['osc1level=0', 'osc2shape=0', 'osc2pulsewidth=64', 'osc2level=%d' % L]),
        ('osc3 saw', lambda L: dict(osc1_level=0, osc3_shape=1, osc3_level=L), lambda L: ['osc1level=0', 'osc3shape=1', 'osc3level=%d' % L]),
        ('osc3 sqr', lambda L: dict(osc1_level=0, osc3_shape=0, osc3_level=L), lambda L: ['osc1level=0', 'osc3shape=0', 'osc3level=%d' % L]))


def level(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    env = np.sqrt(np.convolve(x ** 2, np.ones(r // 200) / (r // 200), 'same'))
    on = np.flatnonzero(env > env.max() * 0.05)[0]
    s = x[on + int(0.3 * r):on + int(1.3 * r)]
    return 10 * np.log10(np.mean((s - s.mean()) ** 2))


def main():
    os.makedirs(OUT, exist_ok=True)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    print('engine - instrument (dB) at Levels %s; instrument level at 127' % ' '.join('%5d' % L for L in LEVELS))
    for name, rig, ren in OSCS:
        row, ref = [], None
        for L in LEVELS:
            hw = os.path.join(OUT, 'hw_%s_l%d.wav' % (name.replace(' ', '_'), L))
            if not os.path.exists(hw):
                p2rig.set_sound(dict(dict(cutoff=127, volume=64), **rig(L)))
                time.sleep(0.4)
                cap = p2rig.capture(hw, 2.5, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(48, 1.5))
                cap.communicate()
            p = os.path.join(os.environ['TMPDIR'], 'osclev.wav')
            subprocess.run([render, '-', '48', '1.5', '0.2', p, '192000', *sq.ENGINE_BASE, 'osc2level=0', 'osc3level=0',
                            'noiselevel=0', 'cutoff=127', 'volume=64', *ren(L)], check=True, capture_output=True)
            h = level(hw, 1.0)
            row.append(level(p, 10.0) - h)
            ref = h
        print('%-9s %s   (%.1f dBFS)' % (name, ' '.join('%+5.1f' % v for v in row), ref))


if __name__ == '__main__':
    main()
