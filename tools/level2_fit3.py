#!/usr/bin/python3
# LEVEL2 as osc 3 (AC coupled) ADDED to osc 2's level control, through a power law with its own floor z and power gamma:
# gain = ((dial + D(L3) x osc 3 - z) / (127 - z))^gamma, the dial capped at `cap`; D(L) = kmax x min(1, ((L - L0) /
# (Lsat - L0))^p). Scored as level2_fit2.py.  usage: level2_fit3.py
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_fit as lf
from level2_fit2 import depth

NAMES = ('tau', 'cap', 'z', 'gamma', 'kmax', 'L0', 'Lsat', 'p')


def model(shape, level2, L3, q):
    tau, cap, z, gamma, kmax, L0, Lsat, p = q
    dial = np.minimum(level2 + depth(L3, kmax, L0, Lsat, p) * lf.control(shape, tau), cap)
    g = lambda d: gamma * np.log(np.clip((d - z) / (127.0 - z), 1e-6, None))
    return g(dial) - g(np.array(min(level2, cap)))


def residuals(q, T):
    r = []
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, q), -5.0)
        hh = np.maximum(h, -5.0)
        r.append(min((np.roll(m, k) - hh for k in range(lf.BINS)), key=lambda d: np.sum(d ** 2)))
    return np.concatenate(r)


if __name__ == '__main__':
    T = lf.takes()
    best = None
    for q0 in ([0.02, 130.0, 12.6, 0.864, 80.0, 4.0, 58.0, 2.0], [0.02, 130.0, 40.0, 3.0, 60.0, 4.0, 58.0, 2.0],
               [0.02, 135.0, 60.0, 6.0, 40.0, 4.0, 58.0, 2.0]):
        fit = least_squares(residuals, q0, args=(T,), bounds=([0.001, 127.0, -50.0, 0.3, 1.0, 0.0, 20.0, 0.5],
                                                              [0.5, 200.0, 63.0, 20.0, 300.0, 14.0, 127.0, 5.0]))
        rms = np.sqrt(np.mean(fit.fun ** 2))
        print('rms %.3f' % rms, ' '.join('%s %.3f' % kv for kv in zip(NAMES, fit.x)), flush=True)
        if best is None or rms < best[0]:
            best = (rms, fit.x)
    q = best[1]
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, q), -5.0)
        hh = np.maximum(h, -5.0)
        m = min((np.roll(m, k) for k in range(lf.BINS)), key=lambda v: np.sum((v - hh) ** 2))
        print('%-16s rms %.2f  mean hw %+.2f fit %+.2f' % (lf.ls.tag(shape, lv, l2), np.sqrt(np.mean((m - hh) ** 2)),
                                                      np.log(np.mean(np.exp(hh))), np.log(np.mean(np.exp(m)))))
