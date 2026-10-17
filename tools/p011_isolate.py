#!/usr/bin/python3
# P011 taken apart: the sound in the edit buffer with its LFO (and then its filter envelope) switched off by CC, on
# the instrument and the engine alike; the sub-octave harmonics (32.7 Hz grid) over time.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/p011'
SYX = '/Volumes/ext-ssd/Captures/Pulse2/192k/patches/fixedlfo_011.syx'
NOTE, F0 = 48, 130.8128 / 4
HOLD = float(os.environ.get('P011_HOLD', '2.0'))
CASES = {'A_nolfo': ({109: 64}, ['mod1amount=64']),
         'B_noenv': ({109: 64, 52: 64}, ['mod1amount=64', 'filterenvamount=64']),
         'C_novel': ({109: 64, 52: 64, 53: 64}, ['mod1amount=64', 'filterenvamount=64', 'filtervelocity=64']),
         'D_nokey': ({109: 64, 52: 64, 53: 64, 51: 64}, ['mod1amount=64', 'filterenvamount=64', 'filtervelocity=64', 'filterkeytrack=64'])}
CASES['F_noampvel'] = ({109: 64, 52: 64, 53: 64, 51: 64, 58: 64},
                       ['mod1amount=64', 'filterenvamount=64', 'filtervelocity=64', 'filterkeytrack=64', 'ampvelocity=64'])
CASES['G_nores'] = ({109: 64, 52: 64, 53: 64, 51: 64, 58: 64, 56: 0},
                    ['mod1amount=64', 'filterenvamount=64', 'filtervelocity=64', 'filterkeytrack=64', 'ampvelocity=64', 'resonance=0'])
CASES['E_open'] = ({50: 127, 56: 0, 49: 0, 52: 64, 53: 64, 51: 64},
                   ['cutoff=127', 'resonance=0', 'filtertype=0', 'filterenvamount=64', 'filtervelocity=64', 'filterkeytrack=64'])
if len(sys.argv) > 1:
    CASES = {k: v for k, v in CASES.items() if k[0] in sys.argv[1]}


def harm(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.01)[0]
    rows = []
    for t0 in (0.1, 0.5, 1.0, 1.6):
        s = x[on + int(t0 * r):on + int((t0 + 0.3) * r)]
        s = s - s.mean()
        t = np.arange(len(s)) / r
        w = np.hanning(len(s))
        a = np.array([abs(np.sum(s * w * np.exp(-2j * np.pi * F0 * k * t))) * 2 / w.sum() for k in range(1, 9)])
        rows.append((t0, 20 * np.log10(np.sqrt(np.mean(s ** 2))), 20 * np.log10(a / a.max() + 1e-9)))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    syx = open(SYX, 'rb').read()
    for tag, (ccs, overrides) in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % tag)
        p2rig.send(syx.hex(), 'sleep:300', *[p2rig.hexmsg(ch, c, v) for c, v in ccs.items()])
        time.sleep(0.3)
        cap = p2rig.capture(hw, HOLD + 2.0, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()
        p2 = os.path.join(OUT, 'p2_%s.wav' % tag)
        subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), SYX, str(NOTE), str(HOLD), '1.0',
                        p2, '192000', *overrides], check=True, capture_output=True)
        for (t0, lh, ah), (_, lp, ap) in zip(harm(hw), harm(p2)):
            print('%s t=%.1f  hw %6.1f | %s' % (tag, t0, lh, ' '.join('%4.0f' % v for v in ah)))
            print('%s       eng %6.1f | %s' % (' ' * len(tag), lp + 20, ' '.join('%4.0f' % v for v in ap)))


if __name__ == '__main__':
    main()
