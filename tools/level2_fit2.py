#!/usr/bin/python3
# LEVEL2 as a law (after level2_fit.py): osc 2's level x exp(g), g = smooth-min(depth(L3) x osc 3 AC coupled,
# ceiling over Level 127's gain), depth(L) = kmax x min(1, ((L - L0) / (Lsat - L0))^p). usage: level2_fit2.py
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_fit as lf

NAMES = ('tau', 'cap', 'sharp', 'kmax', 'L0', 'Lsat', 'p')


def depth(L, kmax, L0, Lsat, p):
    return kmax * min(1.0, max(0.0, (L - L0) / (Lsat - L0)) ** p)


def model(shape, level2, L3, q):
    tau, cap, sharp, kmax, L0, Lsat, p = q
    x = depth(L3, kmax, L0, Lsat, p) * lf.control(shape, tau)
    c = cap - np.log(lf.law(level2) / lf.law(127.0))
    return -np.logaddexp(-sharp * x, -sharp * c) / sharp           # a smooth min(x, c)


def residuals(q, T):
    r = []
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, q), -5.0)
        hh = np.maximum(h, -5.0)
        r.append(min((np.roll(m, k) - hh for k in range(lf.BINS)), key=lambda d: np.sum(d ** 2)))
    return np.concatenate(r)


if __name__ == '__main__':
    T = lf.takes()
    q0 = [0.02, 0.0, 4.0, 7.0, 12.0, 58.0, 2.0]
    fit = least_squares(residuals, q0, args=(T,), bounds=([0.001, -1.0, 0.5, 1.0, 0.0, 20.0, 0.5], [0.5, 2.0, 50.0, 20.0, 14.0, 127.0, 5.0]))
    print('rms %.3f nepers' % np.sqrt(np.mean(fit.fun ** 2)), ' '.join('%s %.4f' % kv for kv in zip(NAMES, fit.x)))
    for L in (15, 30, 45, 58, 75, 127):
        print('  depth at %3d: %.2f' % (L, depth(L, *fit.x[3:])))
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, fit.x), -5.0)
        hh = np.maximum(h, -5.0)
        m = min((np.roll(m, k) for k in range(lf.BINS)), key=lambda v: np.sum((v - hh) ** 2))
        print('%-16s rms %.2f  mean hw %+.2f fit %+.2f' % (lf.ls.tag(shape, lv, l2), np.sqrt(np.mean((m - hh) ** 2)),
                                                      np.log(np.mean(np.exp(hh))), np.log(np.mean(np.exp(m)))))
