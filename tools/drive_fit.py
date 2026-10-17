#!/usr/bin/python3
# Fits the drive curves to drive_session.py's captures, cycle by cycle: x -> gain(Drive) -> clip (ceilings P above,
# N below; one ceiling for FUZZ) -> a one-pole shelf. x is the sine the NONE curve passes at the same input level.
# Each capture and each model output is folded on the 1 kHz period in the frame of its own fundamental.
# usage: drive_fit.py <drive capture dir>
import json, os, sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read
from vol_check import LEVELS, HOLD_S

DRIVES = (0, 32, 64, 96, 127)
BINS = 32
RATE = 192000
F0 = 1000.0


def fold(s, rate):
    t = np.arange(len(s)) / rate
    ph = np.angle(np.sum(s * np.exp(-2j * np.pi * F0 * t)))
    b = np.minimum((((F0 * t + ph / (2 * np.pi) + 0.25) % 1) * BINS).astype(int), BINS - 1)
    c = np.bincount(b, s, BINS) / np.bincount(b, None, BINS)
    return c - c.mean()


def measure(path):
    x2, rate = read(path)
    x = x2[:, 0]
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    start = np.flatnonzero(env > 10 ** (-60 / 20))[0]
    return [fold(x[start + int((i * HOLD_S + 0.6) * rate):start + int((i * HOLD_S + 1.4) * rate)], rate)
            for i in range(len(LEVELS))]


def clip(u, P, N):
    return np.where(u >= 0, P * np.tanh(u / P), N * np.tanh(u / N))


def model(a, g, P, N, mix, fc, bias, hp):
    n = int(RATE / F0) * 40
    k = 1 - np.exp(-2 * np.pi * fc / RATE)
    kh = 1 - np.exp(-2 * np.pi * hp / RATE)
    y, lp, dc = np.empty(n), 0.0, 0.0
    x = g * a * np.sin(2 * np.pi * F0 * np.arange(n) / RATE)
    for i in range(n):
        u = x[i] - dc                       # a coupling capacitor ahead of the clipper, charged by its output
        c = (P * np.tanh((u + bias) / P)) if (u + bias) >= 0 else (N * np.tanh((u + bias) / N))
        dc += kh * c
        lp += k * (c - lp)
        y[i] = (mix * c) + ((1 - mix) * lp)
    return fold(y[-int(RATE / F0) * 4:], RATE)


def fit(curve, amps, rows):
    sym = curve == 'FUZZ'

    def unpack(p):
        P = 10 ** (p[0] / 20)
        N = P if sym else 10 ** (p[1] / 20)
        return P, N, p[2], 10 ** p[3], p[4], 10 ** p[5], 10 ** (np.array(p[6:]) / 20)

    def residuals(p):
        P, N, mix, fc, bias, hp, gs = unpack(p)
        r = []
        for di, d in enumerate(DRIVES):
            for li in range(len(LEVELS)):
                m, h = model(amps[li], gs[di], P, N, mix, fc, bias, hp), rows[d][li]
                r.extend((m - h) / np.abs(h).max())
        return r
    p0 = [-28.0, -31.0, 0.6, 3.3, 0.0, 2.0] + [0.0, 6.0, 12.0, 18.0, 24.0]
    lo = [-50, -50, 0.0, 2.0, -0.2, 0.0] + [-30] * 5
    hi = [0, 0, 1.0, 4.7, 0.2, 3.7] + [60] * 5
    res = least_squares(residuals, p0, bounds=(lo, hi), diff_step=1e-3)
    P, N, mix, fc, bias, hp, gs = unpack(res.x)
    return dict(pos_ceiling=P, neg_ceiling=N, shelf_direct=mix, shelf_hz=fc, bias=bias, coupling_hz=hp,
                gain_db={str(d): 20 * np.log10(g) for d, g in zip(DRIVES, gs)},
                rms_of_peak=float(np.sqrt(np.mean(np.square(res.fun)))))


def main():
    d = sys.argv[1]
    none = measure(os.path.join(d, 'drive_NONE_0.wav'))
    amps = [np.abs(c).max() for c in none]
    out = {}
    for curve in ('TUBE', 'FUZZ'):
        rows = {dr: measure(os.path.join(d, 'drive_%s_%d.wav' % (curve, dr))) for dr in DRIVES}
        out[curve] = fit(curve, amps, rows)
        o = out[curve]
        print('%s: ceilings +%.4f / -%.4f, bias %+.4f, coupling %.0f Hz, shelf %.2f direct + low-pass at %.0f Hz, gain %s dB; error %.1f%% of peak'
              % (curve, o['pos_ceiling'], o['neg_ceiling'], o['bias'], o['coupling_hz'], o['shelf_direct'], o['shelf_hz'],
                 ' '.join('%s:%.1f' % kv for kv in o['gain_db'].items()), 100 * o['rms_of_peak']))
    out['none_peaks'] = amps
    json.dump(out, open(os.path.join(d, 'drive_fit.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
