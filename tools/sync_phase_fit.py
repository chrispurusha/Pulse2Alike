#!/usr/bin/python3
# sync_phase_session's takes as  a x osc3(t) + b x osc2(t - phi): osc 3's shape (falling saw or square, its main edge at
# t = 0) and osc 2's (falling saw, or a pulse of the width law's duty, high first) - the fit's phi says where osc 2's
# cycle starts against osc 3's, and b's sign which way up osc 2 is. The fold's own start is free (a circular shift).
import os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polarity_session as ps
import sync_phase_session as sp

N = 256
t = np.arange(N) / N


def saw(x):
    return 1.0 - 2.0 * (x % 1.0)


def pulse(x, duty):
    return np.where((x % 1.0) < duty, 1.0, -1.0)


def duty(pw):
    w = pw << 8
    return ((w + 512) * w >> 15) / 65536.0


def fit(h, o3, o2):
    best = None
    for shift in range(N):                       # where the fold starts against osc 3's main edge
        hh = np.roll(h, shift)
        for k in range(N):                       # osc 2's offset
            X = np.stack([o3(t), o2(t - k / N), np.ones(N)], 1)
            c, res, *_ = np.linalg.lstsq(X, hh, rcond=None)
            r = np.sum((X @ c - hh) ** 2)
            if best is None or r < best[0]:
                best = (r, shift, k / N, c)
    r, shift, phi, c = best
    return phi, c, 1 - r / np.sum((h - h.mean()) ** 2)


if __name__ == '__main__':
    shapes3 = {'saw': saw, 'sqr': lambda x: pulse(x, 0.5)}
    jobs = {'B_pw40_o3saw': ('saw', lambda x: pulse(x, duty(40))), 'C_pw40_o3sqr': ('sqr', lambda x: pulse(x, duty(40))),
            'E_saw_o3saw': ('saw', saw), 'F_pw100_o3saw': ('saw', lambda x: pulse(x, duty(100)))}
    for name, (s3, o2) in jobs.items():
        h = ps.cycle(os.path.join(sp.OUT, 'hw_%s.wav' % name), 1.0)
        h = h[::4]
        N2 = len(h)
        tt = np.arange(N2) / N2
        best = None
        for shift in range(N2):
            hh = np.roll(h, shift)
            for k in range(N2):
                X = np.stack([shapes3[s3](tt), o2(tt - k / N2), np.ones(N2)], 1)
                c, *_ = np.linalg.lstsq(X, hh, rcond=None)
                r = np.sum((X @ c - hh) ** 2)
                if best is None or r < best[0]:
                    best = (r, k / N2, c)
        r, phi, c = best
        print('%-14s osc 2 starts %.3f of a cycle after osc 3\'s main edge; osc 3 x %+.3f, osc 2 x %+.3f; fit %.3f' % (
            name, phi, c[0], c[1], 1 - r / np.sum((h - h.mean()) ** 2)))
