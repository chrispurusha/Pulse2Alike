#!/usr/bin/python3
# P006 against this morning's instrument takes (noise_mask_session, note 60, the whole sound and its parts): level per
# window, octave bands, and the noise between the harmonics, for the engine as built or with prototype switches.
import os, subprocess, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import noise_mask_session as m
from osc_analyse import read

OCT = (125, 250, 500, 1000, 2000, 4000, 8000)


def octaves(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    rows = []
    for a, b in m.WINDOWS:
        s = x[on + int(a * r):on + int(b * r)]
        P = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
        f = np.fft.rfftfreq(len(s), 1 / r)
        rows.append([10 * np.log10(P[(f > c / 1.414) & (f < c * 1.414)].sum() + 1e-30) for c in OCT])
    return np.array(rows)


def main():
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp'))
    for tag, (l1, l2, l3, nz) in m.CASES.items():
        subprocess.run(['./p2render', m.SYX, str(m.NOTE), str(m.HOLD), '0.5', os.path.join(d, 'p2_%s.wav' % tag), '192000',
                        'osc1level=%d' % l1, 'osc2level=%d' % l2, 'osc3level=%d' % l3, 'noiselevel=%d' % nz], check=True, capture_output=True)
    for tag in ('all', 'all_nn', 'noise'):
        hw = 10 * np.log10(np.mean([10 ** (octaves(os.path.join(m.OUT, 'hw_%s_%d.wav' % (tag, k)), 1.0) / 10) for k in range(2)], axis=0))
        p2 = octaves(os.path.join(d, 'p2_%s.wav' % tag), 10.0)
        print('%-7s engine - instrument, octaves %s:  %s' % (tag, OCT, ' | '.join(' '.join('%+5.1f' % v for v in row) for row in p2 - hw)))


if __name__ == '__main__':
    main()
