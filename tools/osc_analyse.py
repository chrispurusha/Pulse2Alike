#!/usr/bin/python3
# Analyses an osc_capture.py take: per note, f0 against the DCO law, level, harmonics, and the cycle
# folded on the measured f0 (fractional phase - an integer-lag fold smears the upper harmonics).
# usage: osc_analyse.py <take.wav> [--fold out.csv]     needs numpy (/usr/bin/python3, the Xcode one, has it)
import json, math, sys, wave

import numpy as np

P2_CLOCK = 12e6


def period_ticks(note):
    pitch = note * 256 + 36 * 256
    s, frac = pitch // 256, pitch % 256
    n, octave = s % 12, s // 12
    base = lambda i: math.floor(2 * P2_CLOCK / (440 * 2 ** ((i - 105) / 12)))
    return (base(n) - (((base(n) - base(n + 1)) * frac) >> 8)) >> (octave + 1)


def read(path):
    w = wave.open(path)
    ch, n, rate, width = w.getnchannels(), w.getnframes(), w.getframerate(), w.getsampwidth()
    raw = np.frombuffer(w.readframes(n), dtype=np.uint8)
    if width == 3:      # 24-bit: widen each sample to 32 by putting it in the top three bytes
        b = raw.reshape(-1, 3)
        raw = np.column_stack([np.zeros(len(b), np.uint8), b]).reshape(-1)
        width = 4
    x = np.frombuffer(raw.tobytes(), dtype={2: '<i2', 4: '<i4'}[width]).reshape(-1, ch) / 2.0 ** (8 * width - 1)
    return x, rate


def segments(x, rate, count):
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    on = env > (env.max() * 0.1)
    edges = np.flatnonzero(np.diff(on.astype(int)))
    starts = [e for e in edges if not on[e]][:count]
    return starts


def dft(x, rate, f):
    t = np.arange(len(x)) / rate
    return np.sum(x * np.exp(-2j * np.pi * f * t))


def refine_f0(x, rate, guess, harmonics=4):
    win = np.hanning(len(x))
    xw = x * win
    best = None
    for span in (0.003, 0.0002, 0.00001):
        centre = guess if best is None else best
        fs = centre * (1 + np.linspace(-span, span, 41))
        t = np.arange(len(x)) / rate
        tot = [sum(abs(np.sum(xw * np.exp(-2j * np.pi * f * k * t))) for k in range(1, harmonics + 1)) for f in fs]
        best = fs[int(np.argmax(tot))]
    return best


def main():
    path = sys.argv[1]
    meta = json.load(open(path.rsplit('.', 1)[0] + '.json'))
    x2, rate = read(path)
    x = x2[:, 0]
    starts = segments(x, rate, len(meta['notes']))
    fold_rows = []
    print('note   law Hz      meas Hz    cents   rms dBFS  harmonics 2..12 vs 1/k (dB)')
    ratios = []
    for note, s in zip(meta['notes'], starts):
        a = s + int(0.3 * rate)
        seg = x[a:a + int(0.8 * rate)]
        seg = seg - seg.mean()
        law = P2_CLOCK / period_ticks(note)
        f0 = refine_f0(seg, rate, law)
        ratios.append(f0 / law)
        win = np.hanning(len(seg))
        h = [abs(dft(seg * win, rate, f0 * k)) for k in range(1, 13)]
        rel = [20 * math.log10(h[k - 1] / h[0]) + 20 * math.log10(k) for k in range(2, 13)]
        rms = 20 * math.log10(np.sqrt(np.mean(seg ** 2)))
        print('%3d %11.4f %11.4f %+7.2f %8.1f   %s' % (note, law, f0, 1200 * math.log2(f0 / law), rms,
                                                     ' '.join('%5.1f' % r for r in rel)))
        phase = (np.arange(len(seg)) * f0 / rate) % 1.0
        bins = np.minimum((phase * 256).astype(int), 255)
        cyc = np.bincount(bins, seg, 256) / np.maximum(np.bincount(bins, None, 256), 1)
        fold_rows.append((note, cyc))
    r = np.array(ratios)
    print('clock offset (instrument vs interface): mean %+.1f ppm, spread %.2f ppm' % ((r.mean() - 1) * 1e6, (r.max() - r.min()) * 1e6))
    for note, cyc in fold_rows:
        i = int(np.argmin(np.diff(cyc)))
        print('%3d fold: p-p %.4f  min %.4f max %.4f  steepest drop at bin %d' % (note, cyc.max() - cyc.min(), cyc.min(), cyc.max(), i))
    if '--fold' in sys.argv:
        with open(sys.argv[sys.argv.index('--fold') + 1], 'w') as f:
            f.write('bin,' + ','.join(str(n) for n, _ in fold_rows) + '\n')
            for b in range(256):
                f.write('%d,%s\n' % (b, ','.join('%.6f' % c[b] for _, c in fold_rows)))


if __name__ == '__main__':
    main()
