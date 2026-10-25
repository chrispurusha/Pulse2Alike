#!/usr/bin/python3
# The amp envelope through the VCA at low effective volume (P006: Volume 0, Amp Velocity 95, velocity 100): a saw,
# filter open, Env A 0/39/63/50, a 1.5 s note; level traces on the instrument and the engine.
# usage: vca_env_session.py
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/vca_env'
HOLD = 1.5
CASES = (('vol0_vel95', dict(volume=0, vca_velocity=95), ['volume=0', 'ampvelocity=95']),
         ('vol48', dict(volume=48, vca_velocity=64), ['volume=48', 'ampvelocity=64']),
         ('vol100', dict(volume=100, vca_velocity=64), ['volume=100', 'ampvelocity=64']))
ENV = dict(enva_a=0, enva_d=39, enva_s=63, enva_r=50)
ENV_R = ['ampenvattack=0', 'ampenvdecay=39', 'ampenvsustain=63', 'ampenvrelease=50']
TIMES = np.arange(0.0, HOLD + 0.8, 0.05)


def trace(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    return np.array([10 * np.log10(np.mean(x[on + int(t * r):on + int((t + 0.025) * r)] ** 2) + 1e-20) for t in TIMES])


def main():
    os.makedirs(OUT, exist_ok=True)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    print('t (s)          ' + ' '.join('%5.2f' % t for t in TIMES[::2]))
    for tag, rig, ren in CASES:
        hw = os.path.join(OUT, 'hw_%s.wav' % tag)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(dict(osc1_shape=1, osc1_level=127, cutoff=127), **ENV, **rig))
            time.sleep(0.4)
            cap = p2rig.capture(hw, HOLD + 2.0, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(48, HOLD))
            cap.communicate()
        p = os.path.join(os.environ['TMPDIR'], 'vcaenv.wav')
        subprocess.run([render, '-', '48', str(HOLD), '1.0', p, '192000', *sq.ENGINE_BASE, 'osc1shape=1', 'osc1level=127',
                        'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=127', *ENV_R, *ren], check=True, capture_output=True)
        h, e = trace(hw, 1.0), trace(p, 10.0)
        print('%-10s hw   %s' % (tag, ' '.join('%5.1f' % v for v in h[::2])))
        print('%-10s p2-hw %s' % ('', ' '.join('%+5.1f' % v for v in (e - h)[::2])))


if __name__ == '__main__':
    main()
