#!/usr/bin/python3
# NOTE: the P2_* switches it sets lived in p2Filter.c only while the 2026-10-24 refit was explored, and are gone;
# without them this scores the engine as built (p2Filter notes §9 has the result).
# Refits filter_sat_fit's model for a cheaper stage curve (0 tanh, 2 x/sqrt(1+x^2)): D, the loop input's drive and
# the resonance's slope above 97, with LP24's leak from the input and the pole 1/0.95 over the oscillation.
# usage: curve_fit.py curve D loop kAbove
import os, sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filter_sat_score as fs

curve = int(sys.argv[1])
best = [99.0, None, None]


def f(v):
    D, loop, k = v
    if D < 1 or loop < 0 or not 0 <= k < 0.3:
        return 99.0
    env = dict(P2_LEAK_X='1', P2_CUTOFF_SCALE='1.0526', P2_NEWTON='0', P2_LADDER_CURVE=str(curve),
               P2_LADDER_D='%.4f' % D, P2_LOOP_D='%.4f' % loop, P2_K_ABOVE='%.5f' % k)
    r = fs.score(env)
    c = r['squash1'] + r['squash2'] + 0.3 * r['tone'] + 0.5 * abs(r['so_level']) + r['so_spread'] + \
        2 * abs(r['so_shift']) + 0.3 * np.mean(np.abs(r['levels']))
    if c < best[0]:
        best[:] = [c, list(v), r]
    return c


minimize(f, [float(x) for x in sys.argv[2:5]], method='Nelder-Mead', options=dict(maxfev=45, xatol=0.01, fatol=0.01))
c, v, r = best
print('curve %d: cost %.3f D %.3f loop %.3f kAbove %.5f | squash %.2f/%.2f tone %.2f self-osc %+.2f spread %.2f shift %+.2f levels %s' %
      (curve, c, v[0], v[1], v[2], r['squash1'], r['squash2'], r['tone'], r['so_level'], r['so_spread'], r['so_shift'],
       '/'.join('%+.1f' % x for x in r['levels'])))
