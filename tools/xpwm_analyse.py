#!/usr/bin/python3
# xpwm_session's takes: the lines at m f2 + n f_other, read from a fine spectrum (both pitches found from the takes),
# so what X1-/X3-PWM combine can be read off without the free-running phases.  usage: xpwm_analyse.py
import os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/xpwm'


def spectrum(name):
    x2, r = read(os.path.join(OUT, 'hw_%s.wav' % name))
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.3 * r):on + int(2.3 * r)]
    w = np.blackman(len(s))
    return np.fft.rfftfreq(len(s), 1 / r), np.abs(np.fft.rfft(s * w)) * 2 / w.sum()


def peak(f, X, hz, tol=1.5):
    m = (f > hz - tol) & (f < hz + tol)
    i = np.argmax(X[m])
    return f[m][i], 20 * np.log10(X[m][i] + 1e-12)


def pitch(name, guess):
    f, X = spectrum(name)
    return peak(f, X, guess, 3.0)[0]


if __name__ == '__main__':
    f2 = pitch('ref_o2_pwm_w64', 130.81)
    f3 = pitch('ref_o3_sqr', 130.81 * 2 ** (7 / 12))
    f1 = pitch('ref_o1_pwm_w64', 130.81 * 2 ** (7 / 12))
    print('f2 %.3f  f3 %.3f  f1 %.3f' % (f2, f3, f1))
    lines = [(1, 0), (2, 0), (3, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, -1), (2, -1), (-1, 2), (2, 1), (1, 2), (3, -1), (3, -2)]
    print('%-22s %s' % ('', ' '.join('%7s' % ('%+d,%+d' % l) for l in lines)))
    names = sorted(n for n in os.listdir(OUT) if n.startswith('hw_'))
    for n in names:
        name = n[3:-4]
        if name.endswith('unison'):
            continue
        fo = f1 if name.startswith('x1') or 'o1' in name else f3
        f, X = spectrum(name)
        row = [peak(f, X, abs(m * f2 + k * fo))[1] for m, k in lines]
        print('%-22s %s' % (name, ' '.join('%7.1f' % v for v in row)))


TITLES = dict(osc1_shape='osc1shape', osc1_pw='osc1pulsewidth', osc1_level='osc1level', osc2_shape='osc2shape',
              osc2_pw='osc2pulsewidth', osc2_level='osc2level', osc3_shape='osc3shape', osc3_level='osc3level',
              noise='noiselevel', cutoff='cutoff', resonance='resonance', volume='volume')


def render_engine(folder):
    import subprocess
    import squash_session as sq
    import xpwm_session as xs
    for name, s in xs.CASES.items():
        args = []
        for k, v in dict(xs.BASE, **s).items():
            args.append(('osc1semitone=%d' % (v - 64)) if k == 'osc1_semi' else (('osc3semitone=%d' % (v - 64)) if k == 'osc3_semi' else '%s=%d' % (TITLES[k], v)))
        subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', str(xs.NOTE), str(xs.HOLD), '0.3',
                        os.path.join(folder, 'hw_%s.wav' % name), '192000', *sq.ENGINE_BASE, *args], check=True, capture_output=True)


def compare():
    import tempfile
    global OUT
    hwdir, p2dir = OUT, tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp'))
    render_engine(p2dir)
    f2, f3 = 130.8128, 130.8128 * 2 ** (7 / 12)
    print('engine - instrument, dB at the lines (both read the same way; the engine +20 dB for its render gain)')
    for n in sorted(x for x in os.listdir(hwdir) if x.startswith('hw_x')):
        name = n[3:-4]
        if name.endswith('unison'):
            continue
        rows = []
        for d, g in ((hwdir, 0.0), (p2dir, 20.0)):
            OUT = d
            f, X = spectrum(name)
            fo = f3 * (0.5 if name.startswith('x1') else 1.0)
            lines = [(0, 1), (1, 1), (1, -1), (2, -1), (2, 1), (0, 3), (1, 3)]
            rows.append([peak(f, X, abs(m * f2 + k * fo), 2.5)[1] + g for m, k in lines])
        OUT = hwdir
        print('  %-20s hw %s\n  %-20s d  %s' % (name, ' '.join('%6.1f' % v for v in rows[0]), '', ' '.join('%+6.1f' % (b - a) for a, b in zip(*rows))))
