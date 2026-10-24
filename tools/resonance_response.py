#!/usr/bin/python3
# The resonant peak and bass loss from the noise-alone takes of squash2_session (cutoff 64, resonance 0/41/60/80/92),
# the instrument against the engine (renders in a folder, or made with the prototype switches in the environment).
# usage: resonance_response.py [render]
import os, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash2_session as s2
from osc_analyse import read

CENT = (200, 400, 600, 800, 900, 950, 1000, 1050, 1100, 1200, 1500, 2000, 4000)


def psd(p):
    x2, r = read(p)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.4 * r):on + int(2.2 * r)]
    n = 32768
    P = np.mean([np.abs(np.fft.rfft(s[i:i + n] * np.hanning(n))) ** 2 for i in range(0, len(s) - n, n // 2)], axis=0)
    return np.fft.rfftfreq(n, 1 / r), 10 * np.log10(P)


def response(folder, side, mode=''):
    f, P0 = psd(os.path.join(folder, '%s_%sr0_noise.wav' % (side, mode)))
    rows = {}
    for res in (41, 60, 80, 92):
        _, P = psd(os.path.join(folder, '%s_%sr%d_noise.wav' % (side, mode, res)))
        d = P - P0
        rows[res] = np.array([np.mean(d[(f > c * 0.97) & (f < c * 1.03)]) for c in CENT])
    return rows


def render(env, mode=''):
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp'))
    from concurrent.futures import ThreadPoolExecutor
    names = ['%sr%d_noise' % (m, res) for m in ('', 'lp12_') for res in (0, 41, 60, 80, 92)]
    with ThreadPoolExecutor(10) as ex:
        list(ex.map(lambda n: s2.render(n, s2.CASES[n], env, d), names))
    return d


if __name__ == '__main__':
    folder = render(dict(os.environ)) if 'render' in sys.argv else s2.OUT
    print('dB against resonance 0 at %s Hz; engine - instrument' % ' '.join(str(c) for c in CENT))
    for mode in ('', 'lp12_'):
        hw, p2 = response(s2.OUT, 'hw', mode), response(folder, 'p2', mode)
        for res in hw:
            print('%-5s r%-3d hw %s\n           d  %s' % (mode or 'lp24', res, ' '.join('%5.1f' % v for v in hw[res]),
                                                     ' '.join('%+5.1f' % v for v in p2[res] - hw[res])))
