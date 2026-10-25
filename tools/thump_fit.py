#!/usr/bin/python3
# The VCA's control leaking into its output (the "thump"): the oscillators-off takes in thump/ against the engine
# with P2_FT (size), P2_FT_HZ1/2 (two AC couplings) and P2_FT_Q (power of the VCA gain), first 0.4 s, aligned by
# cross-correlation.  usage: thump_fit.py [fit|show k hz1 hz2 q]
import os, subprocess, sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/thump'
RATE, SPAN = 48000, 0.4
CASES = {'vol127_a0_d34': dict(volume=127, ampenvattack=0, ampenvdecay=34),
         'vol64_a0_d34': dict(volume=64, ampenvattack=0, ampenvdecay=34),
         'vol30_a0_d34': dict(volume=30, ampenvattack=0, ampenvdecay=34),
         'vol127_a20_d34': dict(volume=127, ampenvattack=20, ampenvdecay=34),
         'vol127_a40_d34': dict(volume=127, ampenvattack=40, ampenvdecay=34),
         'vol127_a0_d0': dict(volume=127, ampenvattack=0, ampenvdecay=0),
         'vol127_a0_d80': dict(volume=127, ampenvattack=0, ampenvdecay=80),
         'vol127_a0_s127': dict(volume=127, ampenvattack=0, ampenvdecay=34, ampenvsustain=127),
         'vol127_a0_d34_open': dict(volume=127, ampenvattack=0, ampenvdecay=34, cutoff=127)}
HERE = os.path.dirname(os.path.abspath(__file__))


def hw_take(tag):
    x2, r = read(os.path.join(OUT, 'hw_off_%s.wav' % tag))
    x = x2[:, 0] if x2.ndim > 1 else x2
    x = x[::r // RATE] if r % RATE == 0 else x
    on = np.flatnonzero(np.abs(x) > 0.004)[0]
    return x[on - int(0.02 * RATE):on - int(0.02 * RATE) + int((SPAN + 0.1) * RATE)]


HW = {t: hw_take(t) for t in CASES}


def engine(tag, v):
    o = dict(dict(cutoff=0, ampenvsustain=0, ampenvrelease=57), **CASES[tag])
    path = os.path.join(os.environ['TMPDIR'], 'thump_%s.wav' % tag)
    env = dict(os.environ, P2_FT='%g' % v[0], P2_FT_HZ1='%g' % v[1], P2_FT_HZ2='%g' % v[2], P2_FT_Q='%g' % v[3])
    subprocess.run([os.path.join(HERE, 'p2render'), '-', '48', '0.6', '0.3', path, str(RATE), *sq.ENGINE_BASE,
                    'osc1level=0', 'noiselevel=0', 'filtertype=1', *['%s=%d' % kv for kv in o.items()]],
                   check=True, capture_output=True, env=env)
    x2, _ = read(path)
    return (x2[:, 0] if x2.ndim > 1 else x2) * 10.0


def aligned_error(h, e):
    """Both cut at their own first excursion (the take at 0.02 s by construction), then +-2 ms of cross-correlation."""
    n = int(SPAN * RATE)
    on = np.flatnonzero(np.abs(e) > 0.1 * np.abs(e).max())
    e0 = max(0, (on[0] if len(on) else 0) - int(0.02 * RATE))
    best = None
    for lag in range(-int(0.002 * RATE), int(0.002 * RATE) + 1, 4):
        a = int(0.02 * RATE) - (int(0.02 * RATE) - lag)      # the take's window start
        seg, eng = h[max(0, lag):max(0, lag) + n], e[e0:e0 + n]
        if len(seg) < n or len(eng) < n:
            continue
        err = float(np.sum((seg - eng) ** 2))
        if (best is None) or (err < best[0]):
            best = (err, max(0, lag), e0)
    return best


def cost(v, verbose=False):
    if v[0] <= 0 or v[1] <= 0.05 or v[2] <= 0.05 or v[3] <= 0.2:
        return 1e9
    total = 0.0
    for tag in CASES:
        e = engine(tag, v)
        err, lag, e0 = aligned_error(HW[tag], e)
        total += err
        if verbose:
            n = int(SPAN * RATE)
            h = HW[tag][lag:lag + n]
            print('%-20s hw peak %+.3f min %+.3f | p2 peak %+.3f min %+.3f | rms err %.4f' %
                  (tag, h[np.argmax(np.abs(h))], h.min(), e[e0:e0 + n][np.argmax(np.abs(e[e0:e0 + n]))], e[e0:e0 + n].min(), np.sqrt(err / n)))
    return total


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'show':
        cost([float(a) for a in sys.argv[2:6]], True)
    else:
        r = minimize(cost, [0.04, 6.0, 1.0, 1.0], method='Nelder-Mead', options=dict(maxiter=250, xatol=1e-3, fatol=1e-6))
        print('k %.4f hz1 %.3f hz2 %.3f q %.3f  cost %.5f' % (*r.x, r.fun))
        cost(r.x, True)
