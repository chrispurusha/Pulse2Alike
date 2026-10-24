#!/usr/bin/python3
# The level sweep (drive_sweep/: osc 1's triangle through open LP24, Volume 40) against the engine with the output
# gate (p2Plugin notes §55) and with the old fitted quiet-input loss: output level, and the harmonics' rms, per take.
# usage: drive_gate_check.py <old p2render> [note]
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash_session as sq
from osc_analyse import read

SWEEP = '/Volumes/ext-ssd/Captures/Pulse2/drive_sweep/'


def measure(path, gain, f0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    env = np.sqrt(np.convolve(x ** 2, np.ones(r // 100) / (r // 100), 'same'))
    on = np.flatnonzero(env > env.max() * 0.1)[0]
    s = x[on + int(0.30 * r):on + int(0.65 * r)]
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    h = np.array([abs(np.sum(s * w * np.exp(-2j * np.pi * f0 * k * t))) * 2 / w.sum() for k in range(1, 16)])
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12), 20 * np.log10(h + 1e-12)


def render(binary, level, curve, drive, note, out):
    subprocess.run([binary, '-', str(note), '0.8', '0.2', out, '192000', *sq.ENGINE_BASE, 'osc1shape=2', 'osc1level=%d' % level,
                    'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40', 'filtertype=0',
                    'drivecurve=%d' % curve, 'drive=%d' % drive], check=True, capture_output=True)


if __name__ == '__main__':
    old = sys.argv[1]
    note = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    pre = '' if note == 48 else 'n%d_' % note
    f0 = 440.0 * 2 ** ((note - 69) / 12)
    takes = []
    for n in os.listdir(SWEEP):
        m = re.fullmatch(pre + r'l(\d+)_c([12])_d(\d+)\.wav', n)
        if m:
            takes.append(tuple(int(v) for v in m.groups()))
    takes.sort()
    d = os.environ.get('TMPDIR', '/tmp')

    def one(t):
        level, curve, drive = t
        res = []
        for label, binary in (('old', old), ('new', './p2render')):
            out = os.path.join(d, 'dg_%s_%d_%d_%d.wav' % (label, level, curve, drive))
            render(binary, level, curve, drive, note, out)
            res.append(measure(out, 10.0, f0))
        return t, measure(SWEEP + pre + 'l%d_c%d_d%d.wav' % t, 1.0, f0), res
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(one, takes))
    err = {'old': [], 'new': []}
    print('note %d: level  curve drive | instrument dBFS | old: level err, harm rms | new: level err, harm rms' % note)
    for (level, curve, drive), (lh, hh), ((lo, ho), (ln, hn)) in rows:
        keep = hh > hh.max() - 50
        ro, rn = np.sqrt(np.mean(((ho - hh) - (lo - lh))[keep] ** 2)), np.sqrt(np.mean(((hn - hh) - (ln - lh))[keep] ** 2))
        err['old'].append((lo - lh, ro))
        err['new'].append((ln - lh, rn))
        print('  %3d  %s  %3d | %6.1f | %+5.1f %4.1f | %+5.1f %4.1f' % (level, 'TUBE' if curve == 1 else 'FUZZ', drive, lh, lo - lh, ro, ln - lh, rn))
    for k in err:
        a = np.array(err[k])
        print('%s: level rms %.2f dB (mean %+.2f), harmonics rms mean %.2f dB' % (k, np.sqrt(np.mean(a[:, 0] ** 2)), a[:, 0].mean(), a[:, 1].mean()))
