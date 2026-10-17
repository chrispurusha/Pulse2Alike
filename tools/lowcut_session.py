#!/usr/bin/python3
# The filter's level against cutoff: the saw at note 36 (65.4 Hz) through LP12 and LP24, resonance 0, at nine
# cutoffs; the fundamental's level on the instrument and the engine. usage: lowcut_session.py <outdir>
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

CUTOFFS = (0, 8, 16, 24, 32, 48, 64, 96, 127)
NOTE, F0 = 36, 65.406
HERE = os.path.dirname(os.path.abspath(__file__))
TONE = open('/private/tmp/claude-501/-Users-chris-Documents-GitHub/637963f3-4fcf-4a90-acaa-d2b119322a34/scratchpad/caltone.txt').read().split()


def fundamental(path, gain=1.0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.02)[0]
    s = x[on + int(0.3 * r):on + int(1.0 * r)]
    s = s - s.mean()
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    return 20 * np.log10(abs(np.sum(s * w * np.exp(-2j * np.pi * F0 * t))) * 2 / w.sum() + 1e-12)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for vt, name in ((1, 'LP12'), (0, 'LP24')):
        rows = []
        for c in CUTOFFS:
            hw = os.path.join(outdir, 'hw_%s_c%d.wav' % (name, c))
            if not os.path.exists(hw):
                p2rig.set_sound(dict(volume=40, cutoff=c, resonance=0, vcf_type=vt))
                time.sleep(0.3)
                cap = p2rig.capture(hw, 2.8, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(NOTE, 1.2))
                cap.communicate()
            en = os.path.join(outdir, 'p2_%s_c%d.wav' % (name, c))
            subprocess.run([os.path.join(HERE, 'p2render'), '-', str(NOTE), '1.2', '0.1', en, '192000', *TONE,
                            'cutoff=%d' % c, 'filtertype=%d' % vt], check=True, capture_output=True)
            rows.append((c, fundamental(hw), fundamental(en, 10.0)))
        print('%s: cutoff, fundamental hw / engine dB (difference)' % name)
        for c, h, e in rows:
            print('  %3d  %6.1f / %6.1f  (%+.1f)' % (c, h, e, e - h))


if __name__ == '__main__':
    main()
