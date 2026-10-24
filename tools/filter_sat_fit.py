#!/usr/bin/python3
# NOTE: the P2_* switches it sets lived in p2Filter.c only while the 2026-10-24 refit was explored, and are gone;
# without them this scores the engine as built (p2Filter notes §9 has the result).
# Fits the filter's ladder-stage saturation (curve 3: x / (1 + |Dx|^p)^(1/p)), the loop input's saturation and the
# resonance's slope above 97 together, with LP24's leak from the input (P2_LEAK_X), against filter_sat_score's targets.
# usage: filter_sat_fit.py [D p loopD kAbove]
import os, sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filter_sat_score

N = [0]


def objective(v):
    D, p, loop, kAbove = v
    if (D < 1.0) or (p < 1.5) or (p > 20) or (loop < 0.0) or (kAbove < 0.0) or (kAbove > 0.3):
        return 99.0
    env = dict(P2_LEAK_X='1', P2_LADDER_CURVE='3', P2_LADDER_D='%.4f' % D, P2_LADDER_P='%.4f' % p,
               P2_LOOP_D='%.4f' % loop, P2_K_ABOVE='%.5f' % kAbove)
    r = filter_sat_score.score(env)
    cost = r['squash1'] + r['squash2'] + 0.3 * r['tone'] + 0.5 * abs(r['so_level']) + r['so_spread'] + \
        2.0 * abs(r['so_shift']) + 0.3 * np.mean(np.abs(r['levels']))
    N[0] += 1
    print('%3d D %5.2f p %5.2f loop %4.2f kAbove %.4f -> %.3f  squash %.2f/%.2f tone %.2f self-osc %+.1f (spread %.2f, shift %+.2f) levels %s' %
          (N[0], D, p, loop, kAbove, cost, r['squash1'], r['squash2'], r['tone'], r['so_level'], r['so_spread'], r['so_shift'],
           '/'.join('%+.1f' % x for x in r['levels'])), flush=True)
    return cost


if __name__ == '__main__':
    start = [float(x) for x in sys.argv[1:5]] if len(sys.argv) >= 5 else [7.5, 3.0, 3.1, 0.03]
    res = minimize(objective, start, method='Nelder-Mead',
                   options=dict(maxfev=int(os.environ.get('FIT_EVALS', '80')), xatol=0.01, fatol=0.005,
                                initial_simplex=[start, [start[0] * 1.3] + start[1:], [start[0], start[1] * 1.6] + start[2:],
                                                 start[:2] + [start[2] * 0.5, start[3]], start[:3] + [start[3] * 3]]))
    print('best', res.x, res.fun)
