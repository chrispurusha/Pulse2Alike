#!/usr/bin/python3
# Refits LP12's and LP24's output mix to the saw-through-the-filter captures (lowcut_session.py), which reach far
# below the cutoff: the filter's response is the measured harmonics over a saw's 1/k. The old free-mix fit (sweeps at
# -45 dBFS) could not see the deep stopband and left a leak of the early stages in it.
# usage: filter_mix_fit.py <lowcut capture dir>
import os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read

F0 = 65.406
CUTOFFS = (0, 8, 16, 24, 32, 48, 64, 96, 127)
FLOOR_DB = -95.0
OLD = {'LP24': [-0.0093, 0.0133, -0.0381, 0.1664, -0.8047, 2.3955], 'LP12': [-0.0341, 0.0420, -0.1517, 1.7084, -0.3147, 0.1820]}


def osc_hz(c):
    hz = 23.93 * 2 ** (c / 11.977)
    return hz / (1 + (hz / 23600.0) ** 8) ** (1 / 8)


def harmonics(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.02)[0]
    s = x[on + int(0.3 * r):on + int(1.0 * r)]
    s = s - s.mean()
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    ks = np.arange(1, int(18000 / F0))
    a = np.array([abs(np.sum(s * w * np.exp(-2j * np.pi * F0 * k * t))) for k in ks])
    return ks, 20 * np.log10(a / a[0] + 1e-12)


def response(m, f, fc):
    s = 1j * f
    h1 = 1 / (1 + s / fc)
    core = m[0] + m[1] * h1 + m[2] * h1 ** 2 + m[3] * h1 ** 3 + m[4] * h1 ** 4
    shelf = (1 + s / 250.2) / (1 + s / 179.3)
    top = 1 / ((1 + s / 5715.0) * (1 + s / 42533.0))
    return core * shelf * top


def fit(mode, d):
    data = []
    for c in CUTOFFS:
        p = os.path.join(d, 'hw_%s_c%d.wav' % (mode, c))
        if os.path.exists(p):
            ks, db = harmonics(p)
            data.append((osc_hz(c), ks, db))

    def residuals(m):
        r = []
        for fc, ks, db in data:
            h = response(m, ks * F0, fc)
            pred = 20 * np.log10(np.abs(h) / np.abs(h[0])) - 20 * np.log10(ks)
            ok = db > FLOOR_DB
            r.extend((pred - db)[ok][1:] / (1 + 0.02 * np.abs(db[ok][1:])))   # the passband counts as much as the deep stopband
        return r
    old = OLD[mode]
    m0 = [old[0] + old[1]] + old[2:]
    before = np.sqrt(np.mean(np.square(residuals(m0))))
    # only the leak (input and first stage) is free: the later stages' weights carry the resonant shape, which these
    # captures (resonance 0) cannot check
    res = least_squares(lambda q: residuals([q[0], q[1]] + m0[2:]), m0[:2])
    m = np.array([res.x[0], res.x[1]] + m0[2:])
    after = np.sqrt(np.mean(np.square(residuals(m))))
    print('%s: rms %.2f -> %.2f (weighted dB); input+u %.5f, y1 %.5f, y2 %.5f, y3 %.5f, y4 %.5f' % (mode, before, after, *m))
    return m


def main():
    for mode in ('LP24', 'LP12'):
        fit(mode, sys.argv[1])


if __name__ == '__main__':
    main()
