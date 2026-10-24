#!/usr/bin/python3
# squash_session's second part: does the squash follow the oscillator's SLOPE (pitch x level) or its level alone?
# Filter open, noise 104, osc 1 a triangle at 127 on four notes, a saw on two; the noise between each note's harmonics.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = sq.OUT
CASES = [('tri', 2, n, 127) for n in (36, 48, 60, 72)] + [('saw', 1, n, 127) for n in (48, 72)] + \
        [('tri', 2, 72, 60), ('tri', 2, 72, 90)]


def take(name, shape, note, level, noise):
    hw = os.path.join(OUT, 'hw_%s.wav' % name)
    p2rig.set_sound(dict(osc1_shape=shape, osc1_level=level, noise=noise, cutoff=127, resonance=0, volume=40))
    time.sleep(0.3)
    cap = p2rig.capture(hw, sq.HOLD + 1.5, 192000)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(note, sq.HOLD))
    cap.communicate()
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', str(note), str(sq.HOLD), '0.3',
                    os.path.join(OUT, 'p2_%s.wav' % name), '192000', *sq.ENGINE_BASE, 'osc1shape=%d' % shape,
                    'osc1level=%d' % level, 'noiselevel=%d' % noise, 'cutoff=127', 'resonance=0', 'volume=40'],
                   check=True, capture_output=True)


def name_of(kind, note, level, noise):
    return 'pitch_%s_n%d_o%d_nz%d' % (kind, note, level, noise)


def main():
    if 'analyse' not in sys.argv:
        take(name_of('tri', 48, 0, 104), 2, 48, 0, 104)
        for kind, shape, note, level in CASES:
            take(name_of(kind, note, level, 104), shape, note, level, 104)
            take(name_of(kind, note, level, 0), shape, note, level, 0)
    print('noise between the harmonics against the noise alone, dB (bands %s)' % ' '.join('%d-%d' % b for b in sq.BANDS))
    for side in ('hw', 'p2'):
        sq.F0 = 130.8128
        ref, _ = sq.between_harmonics(os.path.join(OUT, '%s_%s.wav' % (side, name_of('tri', 48, 0, 104))))
        for kind, shape, note, level in CASES:
            sq.F0 = 440.0 * 2 ** ((note - 69) / 12)
            d, _ = sq.between_harmonics(os.path.join(OUT, '%s_%s.wav' % (side, name_of(kind, note, level, 104))))
            o, _ = sq.between_harmonics(os.path.join(OUT, '%s_%s.wav' % (side, name_of(kind, note, level, 0))))
            clean = 10 * np.log10(np.maximum(10 ** (d / 10) - 10 ** (o / 10), 1e-30))
            print('  %s %s note %d level %3d  %s   (osc floor %s)' % (side, kind, note, level, ' '.join('%6.1f' % v for v in clean - ref),
                                                              ' '.join('%5.0f' % v for v in o - ref)))


if __name__ == '__main__':
    main()
