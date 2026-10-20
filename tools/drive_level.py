#!/usr/bin/python3
# The drive's output level against its input level: the instrument's (drive_sweep/, each FUZZ or TUBE take against
# the NONE take at the same osc level and note) beside the engine's drive model run on that same NONE take.
# p2Drive notes §4-5. usage: drive_level.py [curve 1=TUBE 2=FUZZ] [note 48/72/84] [loss: none|out|ceiling]
import os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import read

SWEEP = '/Volumes/ext-ssd/Captures/Pulse2/drive_sweep/'
DRIVES = (0, 16, 32, 64, 127)
DRIVE_AT = (0.0, 16.0, 32.0, 64.0, 96.0, 127.0)
# src/p2Drive.c's shapes: positive, negative, bias, couplingHz, shelfDirect, shelfHz, gainDb at DRIVE_AT
SHAPES = {
    1: (0.0751, 0.0359, -0.200, 103.7, 0.000, 3123.0, (-7.25, -0.68, 5.90, 9.86, 13.18, 15.02)),
    2: (0.0634, 0.0628, -0.182, 29.6, 0.653, 214.0, (0.96, 10.66, 12.78, 16.18, 18.35, 19.71)),
}
WINDOW = (0.30, 0.65)   # seconds after the note's onset: past the attack, before the release


def name(level, curve, drive, note):
    return SWEEP + ('' if note == 48 else 'n%d_' % note) + 'l%d_c%d_d%d.wav' % (level, curve, drive)


def onset(s, rate):
    env = np.sqrt(np.convolve(s ** 2, np.ones(rate // 100) / (rate // 100), 'same'))
    return np.flatnonzero(env > env.max() * 0.1)[0]


def db(v):
    return 20.0 * np.log10(max(v, 1e-12))


# src/p2Drive.c's quiet-input loss (notes §5): knee dB, slope, trim dB at DRIVE_AT, fitted for loss 'ceiling'
LOSS = {
    1: ((-27.43, -30.87, -31.55, -32.51, -32.25, -31.99), (3.25, 3.31, 2.97, 2.73, 2.47, 2.20), (4.87, 2.75, 1.21, 0.76, 0.745, 0.73)),
    2: ((-32.55, -31.07, -31.01, -30.78, -30.77, -30.76), (3.93, 2.01, 1.95, 1.87, 1.855, 1.84), (-0.45, -0.78, -0.44, -0.06, 0.085, 0.23)),
}
METER = (0.003, 0.060, 3.15)   # the input level's meter: attack s, release s, its reading over a triangle's RMS


# The engine's model in the instrument's units (the NONE take is already in them), sample by sample as in C.
# loss: None, 'out' (a gain after the curve) or 'ceiling' (the clipper's ceilings and bias scaled instead)
def model(x, rate, curve, drive, loss=None):
    pos, neg, bias, chz, direct, shz, gains = SHAPES[curve]
    g = 10 ** (np.interp(drive, DRIVE_AT, gains) / 20)
    kc, ks, kd = (1 - np.exp(-2 * np.pi * hz / rate) for hz in (chz, shz, 5.0))
    knee, slope, trim = (np.interp(drive, DRIVE_AT, v) for v in LOSS[curve])
    ka, kr = (1 - np.exp(-1 / (t * rate)) for t in METER[:2])
    coupled = low = dc = power = 0.0
    out = np.empty_like(x)

    for i, v in enumerate(x):
        power += (ka if v * v > power else kr) * (v * v - power)
        level = 10 * np.log10(max(power, 1e-20)) - METER[2]
        f = 10 ** ((trim - slope * max(0.0, knee - level)) / 20) if loss else 1.0
        cf = f if loss == 'ceiling' else 1.0
        u = v * g - coupled + bias * cf
        p, n = pos * cf, neg * cf
        c = p * np.tanh(u / p) if u >= 0 else n * np.tanh(u / n)
        coupled += kc * c
        low += ks * (c - low)
        o = direct * c + (1 - direct) * low - dc
        dc += kd * o
        out[i] = o * (f if loss == 'out' else 1.0)
    return out


def rms_window(s, rate, at):
    a, b = at + int(WINDOW[0] * rate), at + int(WINDOW[1] * rate)
    w = s[a:b] - np.mean(s[a:b])
    return np.sqrt(np.mean(w ** 2))


def main():
    curve = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    note = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    loss = sys.argv[3] if (len(sys.argv) > 3) and (sys.argv[3] != 'none') else None
    levels = sorted({int(f.split('_')[-3][1:]) for f in os.listdir(SWEEP)
                     if f.endswith('_c0_d0.wav') and (f.startswith('n%d_' % note) if note != 48 else f.startswith('l'))})
    print('curve %d note %d loss %s: input dB, then per Drive: instrument dB / model dB / difference' % (curve, note, loss))
    print('  in   ' + ''.join('     d%-3d            ' % d for d in DRIVES))

    for level in levels:
        none, rate = read(name(level, 0, 0, note))
        x = none[:, 0]
        at = onset(x, rate)
        row = '%6.1f' % db(rms_window(x, rate, at))

        for d in DRIVES:
            path = name(level, curve, d, note)

            if not os.path.exists(path):
                row += '  %-19s' % '-'
                continue
            hw, _ = read(path)
            h = hw[:, 0]
            hd = db(rms_window(h, rate, onset(h, rate)))
            span = x[max(0, at - rate // 10):at + int(WINDOW[1] * rate)]
            md = db(rms_window(model(span, rate, curve, d, loss), rate, min(at, rate // 10)))
            row += '  %6.1f %6.1f %+5.1f' % (hd, md, hd - md)
        print(row, flush=True)


if __name__ == '__main__':
    main()
