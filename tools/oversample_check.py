#!/usr/bin/python3
# What the Oversampling setting buys at a 48 kHz host: renders at 1x/2x/4x, and the energy BETWEEN the harmonics
# (aliasing, which lands off them) against the harmonics, 0.3-1.3 s, in dB.  Prototype switches pass through.
import os, subprocess, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash_session as sq
from osc_analyse import read

LIB = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/Patches/Pulse2')
TEST = sq.ENGINE_BASE + ['osc2level=0', 'osc3level=0', 'noiselevel=0', 'resonance=0', 'volume=100']
CASES = [('saw, open, note 96', '-', 96, TEST + ['osc1shape=1', 'osc1level=127', 'cutoff=127']),
         ('pulse, open, note 84', '-', 84, TEST + ['osc1shape=0', 'osc1pulsewidth=100', 'osc1level=127', 'cutoff=127']),
         ('saw, cutoff 110 res 90, note 72', '-', 72, TEST + ['osc1shape=1', 'osc1level=127', 'cutoff=110', 'resonance=90']),
         ('saw + FUZZ drive 100, note 72', '-', 72, TEST + ['osc1shape=1', 'osc1level=127', 'cutoff=127', 'drive=100', 'drivecurve=2']),
         ('saw + TUBE drive 100, note 84', '-', 84, TEST + ['osc1shape=1', 'osc1level=127', 'cutoff=127', 'drive=100', 'drivecurve=1'])]
for n, note in ((3, 60), (6, 72), (13, 72), (7, 84)):
    import glob
    CASES.append(('P%03d note %d' % (n, note), glob.glob(os.path.join(LIB, '%03d *.syx' % n))[0], note, []))


def alias_db(path, note):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    s = x[int(0.4 * r):int(1.4 * r)]
    P = np.abs(np.fft.rfft(s * np.blackman(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / r)
    f0 = 440.0 * 2 ** ((note - 69) / 12.0)
    # the sound's own period: find the true f0 near the note (patches transpose) from the strongest low peak
    band = (f > 20) & (f < 4000)
    fp = f[band][np.argmax(P[band])]
    k = max(1, round(fp / f0 * 4) / 4)
    f0 = fp / max(1, round(fp / f0)) if fp > f0 * 0.9 else fp
    near = np.abs(f / f0 - np.round(f / f0)) * f0 < 6.0
    audible = (f > 20) & (f < 20000)
    return 10 * np.log10(P[audible & ~near].sum() / P[audible & near].sum())


if __name__ == '__main__':
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp'))
    print('energy off the harmonics against on them, dB (lower = cleaner); 1x / 2x / 4x')
    for label, syx, note, ov in CASES:
        row = []
        for o in (0, 1, 2):
            p = os.path.join(d, 'o%d.wav' % o)
            subprocess.run(['./p2render', syx, str(note), '1.5', '0.1', p, '48000', *ov, 'oversampling=%d' % o], check=True, capture_output=True)
            row.append(alias_db(p, note))
        print('  %-34s %6.1f %6.1f %6.1f' % (label, *row))
