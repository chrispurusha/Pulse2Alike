#!/usr/bin/python3
# LEVEL2 (after level2_fit4.py), osc 2 Levels 40/64/80/101/127: depth x ((127 - z) / (L2 - z))^q, the boost's
# ceiling gamma x the headroom to Level 127 plus cap.  Scores shape and mean level.  usage: level2_fit5.py
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_fit as lf
from level2_fit2 import depth

NAMES = ('tau', 'cap', 'sharp', 'kmax', 'Lsat', 'p', 'z', 'q', 'gamma')


def model(shape, level2, L3, v):
    tau, cap, sharp, kmax, Lsat, p, z, q, gamma = v
    x = depth(L3, kmax, 0.0, Lsat, p) * ((127.0 - z) / max(1.0, level2 - z)) ** q * lf.control(shape, tau)
    c = cap - gamma * np.log(lf.law(level2) / lf.law(127.0))
    return -np.logaddexp(-sharp * x, -sharp * c) / sharp


def residuals(v, T):
    r = []
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, v), -5.0)
        hh = np.maximum(h, -5.0)
        d = min((np.roll(m, k) - hh for k in range(lf.BINS)), key=lambda e: np.sum(e ** 2))
        mean = np.log(np.mean(np.exp(m))) - np.log(np.mean(np.exp(hh)))
        r.append(np.concatenate([d, [mean * 6.0]]))             # the mean level weighted as six bins
    return np.concatenate(r)


if __name__ == '__main__':
    T = lf.takes()
    fit = least_squares(residuals, [0.027, -0.075, 3.9, 4.0, 59.0, 2.7, 20.0, 1.0, 1.0], args=(T,),
                        bounds=([0.003, -1.0, 0.5, 0.5, 20.0, 0.5, -60.0, 0.2, 0.0], [0.3, 2.0, 50.0, 30.0, 127.0, 5.0, 38.0, 4.0, 3.0]))
    v = fit.x
    print(' '.join('%s %.4f' % kv for kv in zip(NAMES, v)))
    means = []
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, lv, v), -5.0)
        hh = np.maximum(h, -5.0)
        m2 = min((np.roll(m, k) for k in range(lf.BINS)), key=lambda e: np.sum((e - hh) ** 2))
        dm = 8.686 * (np.log(np.mean(np.exp(m))) - np.log(np.mean(np.exp(hh))))
        means.append(dm)
        print('%-16s shape rms %.2f  mean %+5.1f dB' % (lf.ls.tag(shape, lv, l2), np.sqrt(np.mean((m2 - hh) ** 2)), dm))
    print('mean level rms %.1f dB' % np.sqrt(np.mean(np.square(means))))
