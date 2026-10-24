#!/usr/bin/python3
# Does an oscillator lower the noise? P006 taken apart by oscillator levels (CC 45/46/47, noise CC 48), on the
# instrument (edit buffer) and the engine alike; the noise read between the harmonics of note 60's sub-octave (all
# three oscillators sit on it, osc 3 synced), per band and window, against the noise alone.
# usage: noise_mask_session.py [capture|analyse]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/noise_mask'
SYX = '/Volumes/ext-ssd/Captures/Pulse2/192k/patches/fixedlfo_006.syx'
NOTE, F0, HOLD, TAKES = 60, 130.8128, 3.0, 2
CASES = {'noise':  (0, 0, 0, 104),
         'osc1':   (120, 0, 0, 104),
         'osc2':   (0, 101, 0, 104),
         'osc23':  (0, 101, 58, 104),
         'all':    (120, 101, 58, 104),
         'all_nn': (120, 101, 58, 0)}
BANDS = ((150, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000))
WINDOWS = ((0.1, 0.6), (0.6, 1.6), (1.6, 2.8))


def capture():
    os.makedirs(OUT, exist_ok=True)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    syx = open(SYX, 'rb').read()
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    for tag, (l1, l2, l3, nz) in CASES.items():
        for take in range(TAKES):
            hw = os.path.join(OUT, 'hw_%s_%d.wav' % (tag, take))
            p2rig.send(syx.hex(), 'sleep:300', *[p2rig.hexmsg(ch, c, v) for c, v in ((45, l1), (46, l2), (47, l3), (48, nz))])
            time.sleep(0.3)
            cap = p2rig.capture(hw, HOLD + 2.0, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(NOTE, HOLD))
            cap.communicate()
        subprocess.run([render, SYX, str(NOTE), str(HOLD), '0.5', os.path.join(OUT, 'p2_%s.wav' % tag), '192000',
                        'osc1level=%d' % l1, 'osc2level=%d' % l2, 'osc3level=%d' % l3, 'noiselevel=%d' % nz],
                       check=True, capture_output=True)


def between_harmonics(path):
    """Mean power density between the harmonics, [window][band], in dB."""
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    rows = []
    for a, b in WINDOWS:
        s = x[on + int(a * r):on + int(b * r)]
        w = np.hanning(len(s))
        p = np.abs(np.fft.rfft((s - s.mean()) * w)) ** 2 / (w ** 2).sum()
        f = np.fft.rfftfreq(len(s), 1 / r)
        gap = np.abs(f / F0 - np.round(f / F0)) * F0 > 12.0
        rows.append([10 * np.log10(p[gap & (f >= lo) & (f < hi)].mean()) for lo, hi in BANDS])
    return np.array(rows)


def power(db):
    return 10 ** (db / 10)


def analyse():
    for side in ('hw', 'p2'):
        def level(tag):
            if side == 'p2':
                return between_harmonics(os.path.join(OUT, 'p2_%s.wav' % tag))
            takes = [power(between_harmonics(os.path.join(OUT, 'hw_%s_%d.wav' % (tag, k)))) for k in range(TAKES)]
            return 10 * np.log10(np.mean(takes, axis=0))
        ref = level('noise')
        floor = power(level('all_nn'))
        print('\n%s: noise between the harmonics, dB against the noise alone (bands %s)' % (side, ' '.join('%d-%d' % b for b in BANDS)))
        for tag in CASES:
            if tag == 'noise':
                print('  %-7s ' % tag + ' | '.join(' '.join('%6.1f' % v for v in row) for row in ref))
                continue
            d = level(tag)
            if tag == 'all':
                clean = 10 * np.log10(np.maximum(power(d) - floor, 1e-30))
                print('  %-7s ' % 'all-osc' + ' | '.join(' '.join('%6.1f' % v for v in row) for row in clean - ref))
            print('  %-7s ' % tag + ' | '.join(' '.join('%6.1f' % v for v in row) for row in d - ref))


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if mode in ('capture', 'both'):
        capture()
    if mode in ('analyse', 'both'):
        analyse()
