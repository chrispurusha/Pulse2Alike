#!/usr/bin/python3
# What osc 1's Keytrack does in unison (the manual: it "controls the detuning"): UNISON-M, Unison Detune 42, PW 64,
# Keytrack ON and OFF, notes 36 and 72; the cluster's spread around the fundamental, instrument and engine.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/unison_key'
CASES = [(k, n) for k in (1, 0) for n in (36, 72)]


def spread(path, note, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.3 * r):on + int(3.8 * r)]
    X = np.abs(np.fft.rfft(s * np.blackman(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / r)
    f0 = 440.0 * 2 ** ((note - 69) / 12)
    m = (f > f0 * 0.9) & (f < f0 * 1.1)
    p = X[m] / X[m].sum()
    cents = 1200 * np.log2(f[m] / f0)
    mean = np.sum(p * cents)
    return mean, np.sqrt(np.sum(p * (cents - mean) ** 2))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for key, note in CASES:
        hw = os.path.join(OUT, 'hw_k%d_n%d.wav' % (key, note))
        if not os.path.exists(hw):
            p2rig.set_sound(dict(osc1_shape=4, osc1_pw=64, osc1_level=127, osc1_keytrack=key, unison_detune=42, cutoff=127, volume=40))
            time.sleep(0.3)
            cap = p2rig.capture(hw, 5.0, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(note, 4.0))
            cap.communicate()
        p2 = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'uk.wav')
        subprocess.run(['./p2render', '-', str(note), '4.0', '0.2', p2, '192000', *sq.ENGINE_BASE, 'osc1shape=4', 'osc1pulsewidth=64',
                        'osc1level=127', 'osc1keytrack=%d' % key, 'unisondetune=42', 'cutoff=127', 'volume=40', 'noiselevel=0'],
                       check=True, capture_output=True)
        (mh, sh), (mp, sp) = spread(hw, note, 1.0), spread(p2, note, 10.0)
        print('keytrack %d note %d: instrument centre %+.1f cents, spread %.1f | engine %+.1f, %.1f' % (key, note, mh, sh, mp, sp))
