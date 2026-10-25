#!/usr/bin/python3
# Pulses' top octaves, engine minus instrument, against the takes in para_width/ (filter open, note 48):
# PWM, PARA-8 and PARA-4 at widths 20/64/110, the saw as the flat reference.  usage: pulse_top_check.py
import os, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash_session as sq
from osc_analyse import read

D = '/Volumes/ext-ssd/Captures/Pulse2/192k/para_width'
OCT = (500, 1000, 2000, 4000, 8000, 16000)


def bands(path, g):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * g
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.4 * r):on + int(1.8 * r)]
    S = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / r)
    return np.array([10 * np.log10(S[(f >= c / np.sqrt(2)) & (f < c * np.sqrt(2))].sum()) for c in OCT])


def row(hw, shape, extra):
    p = os.path.join(os.environ['TMPDIR'], 'ptc.wav')
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', '48', '2.0', '0.2', p, '192000',
                    *sq.ENGINE_BASE, 'osc1shape=%d' % shape, 'osc1level=127', 'osc2level=0', 'osc3level=0', 'noiselevel=0',
                    'cutoff=127', 'volume=40', *extra], check=True, capture_output=True)
    d = bands(p, 10.0) - bands(os.path.join(D, hw), 1.0)
    return ' '.join('%+5.1f' % v for v in d) + '   tilt (16k - 1k) %+5.1f' % (d[-1] - d[1])


if __name__ == '__main__':
    print('engine - instrument, octaves', OCT)
    print('%-12s %s' % ('SAW', row('hw_SAW_n48.wav', 1, [])))
    for shape, name in ((0, 'PWM'), (8, 'PARA8'), (9, 'PARA4')):
        for wd in (20, 64, 110):
            print('%-12s %s' % ('%s w%d' % (name, wd), row('hw_%s_w%d.wav' % (name, wd), shape, ['osc1pulsewidth=%d' % wd, 'osc2pulsewidth=%d' % wd])))
