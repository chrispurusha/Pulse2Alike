#!/usr/bin/python3
# LEVEL2 (after level2_fit2.py): the exponential law with its depth scaled by (127 - z) / (Level2 - z), so osc 3 swings
# osc 2 further when osc 2 is set lower.  usage: level2_fit4.py
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_fit as lf
from level2_fit2 import depth

NAMES = ('tau', 'cap', 'sharp', 'kmax', 'L0', 'Lsat', 'p', 'z')


def model(shape, level2, L3, q):
    tau, cap, sharp, kmax, L0, Lsat, p, z = q
    x = depth(L3, kmax, L0, Lsat, p) * ((127.0 - z) / max(1.0, level2 - z)) * lf.control(shape, tau)
    c = cap - np.log(lf.law(level2) / lf.law(127.0))
    return -np.logaddexp(-sharp * x, -sharp * c) / sharp


def residuals(q, T):
    r = []
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, q), -5.0)
        hh = np.maximum(h, -5.0)
        r.append(min((np.roll(m, k) - hh for k in range(lf.BINS)), key=lambda d: np.sum(d ** 2)))
    return np.concatenate(r)


if __name__ == '__main__':
    T = lf.takes()
    fit = least_squares(residuals, [0.02, 0.0, 4.0, 7.0, 4.0, 58.0, 2.5, 40.0], args=(T,),
                        bounds=([0.001, -1.0, 0.5, 0.5, 0.0, 20.0, 0.5, -100.0], [0.5, 2.0, 50.0, 30.0, 14.0, 127.0, 5.0, 62.0]))
    q = fit.x
    print('rms %.3f nepers' % np.sqrt(np.mean(fit.fun ** 2)), ' '.join('%s %.4f' % kv for kv in zip(NAMES, q)))
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, q), -5.0)
        hh = np.maximum(h, -5.0)
        m = min((np.roll(m, k) for k in range(lf.BINS)), key=lambda v: np.sum((v - hh) ** 2))
        print('%-16s rms %.2f  mean hw %+.2f fit %+.2f' % (lf.ls.tag(shape, lv, l2), np.sqrt(np.mean((m - hh) ** 2)),
                                                      np.log(np.mean(np.exp(hh))), np.log(np.mean(np.exp(m)))))
