#!/usr/bin/python3
# P006's LEVEL2 path alone (osc 1 and noise off, filter open, envelope flat): the instrument against engine builds -
# harmonics 1-24 of the note (dB against the fundamental) and the level, notes 48 and 60.
# usage: p006_level2_check.py <p2render> [<p2render> ...]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/p006_level2'
SYX = '/Volumes/ext-ssd/Captures/Pulse2/192k/patches/fixedlfo_006.syx'
CCS = ((45, 0), (48, 0), (50, 127), (52, 64), (56, 0), (53, 64), (51, 64))
OVR = ['osc1level=0', 'noiselevel=0', 'cutoff=127', 'filterenvamount=64', 'resonance=0', 'filtervelocity=64', 'filterkeytrack=64']


def spectrum(path, gain, note):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.4 * r):on + int(1.4 * r)]
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    f0 = 440.0 * 2 ** ((note - 12 - 69) / 12)          # osc 3 (the sync master) at -12
    h = np.array([abs(np.sum(s * w * np.exp(-2j * np.pi * f0 * k * t))) * 2 / w.sum() for k in range(1, 25)])
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12), 20 * np.log10(h + 1e-12)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    for note in (48, 60):
        hw = os.path.join(OUT, 'hw_n%d.wav' % note)
        if not os.path.exists(hw):
            p2rig.send(open(SYX, 'rb').read().hex(), 'sleep:300', *[p2rig.hexmsg(ch, c, v) for c, v in CCS])
            time.sleep(0.3)
            cap = p2rig.capture(hw, 2.6, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(note, 1.6))
            cap.communicate()
        lh, hh = spectrum(hw, 1.0, note)
        print('note %d: instrument level %.1f dBFS, harmonics against the 1st: %s' % (note, lh, ' '.join('%+4.0f' % v for v in (hh - hh[0])[:16])))
        for b in sys.argv[1:]:
            p = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'p6l2.wav')
            subprocess.run([b, SYX, str(note), '1.6', '0.3', p, '192000', *OVR], check=True, capture_output=True)
            le, he = spectrum(p, 10.0, note)
            keep = hh > hh.max() - 45
            d = (he - hh) - np.median((he - hh)[keep])
            print('   %-28s level %+5.1f dB, harmonic rms %.1f dB: %s' % (os.path.basename(b), le - lh, np.sqrt(np.mean(d[keep] ** 2)),
                                                                   ' '.join('%+4.0f' % v for v in (he - he[0])[:16])))
