#!/usr/bin/python3
# Fits LEVEL2 as osc 3 (AC coupled) ADDED to osc 2's Level dial, through osc 2's level law, clamped to [0, cap] - to
# level2_session's folds (log of osc 2's envelope over osc 3's period, against osc 3 at 0).  usage: level2_fit.py
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_session as ls

BINS = 128
F3 = ls.F3


def law(dial):
    """The instrument's oscillator level law (p2Plugin notes §36)."""
    return np.power(np.clip((dial - 12.6) / 114.4, 1e-6, None), 0.864)


def control(shape, tau, steps=BINS * 6):
    """osc 3 at 16.35 Hz through a one-pole high-pass, its last cycle in BINS bins, reset at bin 0."""
    t = (np.arange(steps) % BINS) / BINS
    x = (1.0 - 2.0 * t) if shape == 'saw' else np.where(t < 0.5, 1.0, -1.0)     # falling ramp; square high first
    dt = 1.0 / (F3 * BINS)
    a = np.exp(-dt / tau) if tau > 0 else 0.0
    y = np.zeros(steps)
    lp = 0.0
    for i in range(steps):
        lp = lp + (1 - a) * (x[i] - lp)
        y[i] = x[i] - lp
    return y[-BINS:]


def model(shape, level2, depth, tau, cap, sign):
    """osc 2's own level x exp(depth x osc 3, AC coupled), no higher than cap nepers over Level 127's gain."""
    c = control(shape, tau)
    g = np.minimum(sign * depth * c, cap - np.log(law(level2) / law(127.0)))
    j = np.argmax(np.abs(np.diff(g, append=g[0]))) + 1
    return np.roll(g, -j)


def takes():
    out = []
    for shape, s3, lv, l2 in ls.CASES:
        if lv == 0:
            continue
        h = ls.fold(os.path.join(ls.OUT, 'hw_%s.wav' % ls.tag(shape, lv, l2)), 1.0, BINS)
        h0 = np.mean(ls.fold(os.path.join(ls.OUT, 'hw_%s.wav' % ls.tag(shape, 0, l2)), 1.0, BINS))
        out.append((shape, lv, l2, np.log(h / h0)))
    return out


LV = (15, 30, 45, 58, 75, 90, 110, 127)

if __name__ == '__main__':
    T = takes()
    best = None
    for sign in (1.0, -1.0):
        def f(p):
            tau, cap = p[0], p[1]
            depth = dict(zip(LV, p[2:]))
            r = []
            for shape, lv, l2, h in T:
                m = np.maximum(model(shape, l2, depth[lv], tau, cap, sign), -5.0)
                hh = np.maximum(h, -5.0)                                     # below -5 nepers is the floor
                best = min((np.roll(m, k) - hh for k in range(BINS)), key=lambda d: np.sum(d ** 2))
                r.append(best)
            return np.concatenate(r)
        p0 = [0.010, 0.2] + [lv / 30.0 for lv in LV]
        fit = least_squares(f, p0, bounds=([0.001, -1.0] + [0.0] * len(LV), [0.5, 2.0] + [20.0] * len(LV)))
        rms = np.sqrt(np.mean(fit.fun ** 2))
        print('sign %+d: rms %.3f nepers  tau %.4f s  cap %.3f nepers  depth (nepers/unit) %s' % (sign, rms, fit.x[0], fit.x[1],
              ' '.join('%d:%.2f' % (lv, d) for lv, d in zip(LV, fit.x[2:]))))
        if best is None or rms < best[0]:
            best = (rms, sign, fit.x)
    rms, sign, x = best
    depth = dict(zip(LV, x[2:]))
    for shape, lv, l2, h in T:
        m = np.maximum(model(shape, l2, depth[lv], x[0], x[1], sign), -5.0)
        hh = np.maximum(h, -5.0)
        m = min((np.roll(m, k) for k in range(BINS)), key=lambda v: np.sum((v - hh) ** 2))
        print('%-16s hw  %s\n%-16s fit %s' % (ls.tag(shape, lv, l2), ' '.join('%+5.2f' % v for v in h[::8]), '',
                                              ' '.join('%+5.2f' % v for v in m[::8])))
