#!/usr/bin/python3
# Fits the drive curve (tools/drive_model.c, as src/p2Drive.c) to the WAVEFORM as well as the harmonics: for every
# drive_sweep/ take at note 48 the model runs on the NONE take, one cycle is averaged phase-locked, aligned to the
# instrument's by circular shift, and the difference is scored in the instrument's units beside the harmonic residual
# of tools/drive_shape.py. Harmonic levels ignore phase, and a harmonic-only fit (p2Drive notes §6) found a FUZZ that
# ramps where the instrument curves, and a TUBE too square at high Drive, both heard and measured on the 2026-10-26
# init-triangle takes (192k/drive_init_tri/). p2Drive notes §8.
# Stage 'asym' then adds a negative-ceiling scale and a bias per Drive on top of a saved fit (p2Drive notes §9).
# usage: drive_wave.py <curve 1=TUBE 2=FUZZ> [fit|score|asym] [state.json]
import json, os, sys, tempfile

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive_shape as ds
from drive_shape import harmonics, residual, DRIVES, GATE_DB, LIB, DP
import ctypes
from osc_analyse import read
from drive_level import name, onset, WINDOW

DIRECT_PER_DRIVE = [False]       # stage 'asym2': the per-Drive slot is the shelf's direct share, not the bias
MIN_LEVEL = 24                   # osc Level where the output gate is fully open (p2Plugin notes §55); quieter takes sit near the noise
N = 256                          # points in the averaged cycle
WAVE_WEIGHT = 40.0               # a cycle error of 1/40 of its peak weighs as 1 dB of harmonic error
P2DRIVE_AT = (0.0, 16.0, 32.0, 64.0, 96.0, 127.0)
# src/p2Drive.c as of 2026-10-26: shape (pos, neg, bias, couplingHz, shelfDirect, shelfHz, hardPos, hardNeg),
# gainDb and trimDb at P2DRIVE_AT
ENGINE = {
    1: ([0.0835, 0.0360, 0.495, 105.2, 0.925, 19119.0, 1.707, 1.955],
        [-8.37, -0.93, 3.55, 8.16, 10.51, 12.78], [3.51, 1.78, 1.38, 0.57, 0.83, 1.08]),
    2: ([0.0697, 0.0676, -0.0375, 388.1, 0.552, 139.3, 12.55, 12.55],
        [10.97, 16.67, 18.84, 22.27, 29.26, 36.03], [-5.10, -2.39, -0.95, 0.04, 0.74, 1.41]),
}


def run(x, rate, shape, gain, loss, neg_scale=1.0):
    x = np.ascontiguousarray(x, dtype=np.float64)
    out = np.empty_like(x)
    sh = np.ascontiguousarray(shape, dtype=np.float64)
    ls = np.ascontiguousarray(loss, dtype=np.float64)
    LIB.drive_run2(x.ctypes.data_as(DP), len(x), ctypes.c_double(rate), sh.ctypes.data_as(DP), ctypes.c_double(gain),
                   ls.ctypes.data_as(DP), ctypes.c_double(neg_scale), out.ctypes.data_as(DP))
    return out


def cycle(s, rate, f0):
    t = np.arange(len(s)) / rate
    b = (((t * f0) % 1.0) * N).astype(int)
    return np.bincount(b, s, N) / np.maximum(np.bincount(b, None, N), 1)


def aligned(model, hw):
    c = [np.dot(np.roll(model, k), hw) for k in range(N)]
    return np.roll(model, int(np.argmax(c)))


def hw_cycles(curve, takes):
    cyc = {}
    for level in sorted({int(f.split('_')[0][1:]) for f in os.listdir(ds.SWEEP) if f.startswith('l') and f.endswith('_c0_d0.wav')}):
        if level <= 12:
            continue
        for d in DRIVES:
            p = name(level, curve, d, 48)
            if os.path.exists(p):
                h, rate = read(p)
                h = h[:, 0]
                ah = onset(h, rate)
                cyc[(level, d)] = h[ah + int(WINDOW[0] * rate):ah + int(WINDOW[1] * rate)]
    return cyc


def build(curve):
    takes = [t for t in ds.load(curve) if t[2] == 48]
    levels = sorted({int(f.split('_')[0][1:]) for f in os.listdir(ds.SWEEP) if f.startswith('l') and f.endswith('_c0_d0.wav')})
    levels = [l for l in levels if l > 12]
    # ds.load walks levels in order and drives in order, skipping missing files: rebuild the same order
    keys = [(l, d) for l in levels for d in DRIVES if os.path.exists(name(l, curve, d, 48))]
    assert len(keys) == len(takes), (len(keys), len(takes))
    hws = hw_cycles(curve, takes)
    rows = []
    for (l, d), t in zip(keys, takes):
        if l < MIN_LEVEL:
            continue
        f0 = t[5]
        rows.append(dict(level=l, drive=d, t=t, hw=cycle(hws[(l, d)], t[6], f0), gate=10 ** (GATE_DB.get(id(t[3]), 0.0) / 20)))
    return rows


def model_out(row, shape, gain_db, trim_db, neg_scale=1.0, bias=None):
    d, _, _, span, _, f0, rate, a, b = row['t']
    if bias is not None:
        shape = list(shape)
        shape[4 if DIRECT_PER_DRIVE[0] else 2] = bias
    y = run(span, rate, shape, 10 ** (gain_db / 20), [-1000.0, 1e-9, trim_db], neg_scale) * row['gate']   # a loss that never engages: the trim alone
    return y[a:b], f0, rate


def residuals(row, shape, gain_db, trim_db, neg_scale=1.0, bias=None):
    y, f0, rate = model_out(row, shape, gain_db, trim_db, neg_scale, bias)
    mc = aligned(cycle(y, rate, f0), row['hw'])
    peak = max(1e-9, np.max(np.abs(row['hw'])))
    wave = (mc - row['hw']) / peak * WAVE_WEIGHT / np.sqrt(N / 16)
    harm = residual(row['t'], harmonics(y, rate, f0) + 20 * np.log10(1.0))
    return wave, harm


def scores(rows, shape, gains, trims, negs=None, biases=None):
    w, h = [], []
    for r in rows:
        i = DRIVES.index(r['drive'])
        a, b = residuals(r, shape, gains[i], trims[i], 1.0 if negs is None else negs[i], None if biases is None else biases[i])
        w.append(np.sqrt(np.mean((a / WAVE_WEIGHT * np.sqrt(N / 16)) ** 2)) * 100)
        h.append(np.sqrt(np.mean(b ** 2)))
    return np.mean(w), np.mean(h), w, h


def main():
    curve = int(sys.argv[1])
    stage = sys.argv[2] if len(sys.argv) > 2 else 'fit'
    saved = sys.argv[3] if len(sys.argv) > 3 else os.path.join(tempfile.gettempdir(), 'p2_drive_wave_%d.json' % curve)
    ds.APPLY_GATE[0] = True
    rows = build(curve)
    shape0, g6, t6 = ENGINE[curve]
    gains0 = [float(np.interp(d, P2DRIVE_AT, g6)) for d in DRIVES]
    trims0 = [float(np.interp(d, P2DRIVE_AT, t6)) for d in DRIVES]
    w, h, _, _ = scores(rows, shape0, gains0, trims0)
    print('engine now: cycle error %.1f%% of peak, harmonic rms %.2f dB over %d takes' % (w, h, len(rows)), flush=True)
    if stage == 'score':
        st = json.load(open(saved))
        w, h, ws, hs = scores(rows, st['shape'], st['gains'], st['trims'])
        print('saved fit:  cycle error %.1f%% of peak, harmonic rms %.2f dB' % (w, h))
        for r, a, b in zip(rows, ws, hs):
            print('  level %3d drive %3d: cycle %5.1f%%  harmonics %5.2f dB' % (r['level'], r['drive'], a, b))
        return
    n = len(DRIVES)
    if stage == 'asym2':
        DIRECT_PER_DRIVE[0] = True
    if stage in ('asym', 'asym2'):
        st = json.load(open(saved))
        shape, gains, trims = st['shape'], st['gains'], st['trims']
        w, h, _, _ = scores(rows, shape, gains, trims)
        print('waveform fit: cycle error %.1f%% of peak, harmonic rms %.2f dB' % (w, h), flush=True)
        lo = [0.005, 0.005, 1.0, 0.0, 20.0, 0.5, 0.5] + [-20.0] * n + [-12.0] * n + [0.3] * n + ([0.0] * n if DIRECT_PER_DRIVE[0] else [-0.6] * n)
        hi = [0.5, 0.5, 3000.0, 1.0, 20000.0, 30.0, 30.0] + [60.0] * n + [12.0] * n + [3.0] * n + ([1.0] * n if DIRECT_PER_DRIVE[0] else [0.6] * n)
        start = [shape[0], shape[1]] + list(shape[3:]) + list(gains) + list(trims) + [1.0] * n + ([shape[4]] * n if DIRECT_PER_DRIVE[0] else [shape[2]] * n)
        start = [min(max(v, l + 1e-6), u - 1e-6) for v, l, u in zip(start, lo, hi)]

        def unpack_a(p):
            p = list(p)
            sh = p[:2] + [0.0] + p[2:7]
            return sh, p[7:7 + n], p[7 + n:7 + 2 * n], p[7 + 2 * n:7 + 3 * n], p[7 + 3 * n:7 + 4 * n]

        def fa(p):
            sh, g, t, ng, bs = unpack_a(p)
            out = []
            for r in rows:
                i = DRIVES.index(r['drive'])
                a, b = residuals(r, sh, g[i], t[i], ng[i], bs[i])
                out += [a, b]
            return np.concatenate(out)
        fit = least_squares(fa, start, bounds=(lo, hi), x_scale='jac', diff_step=1e-3, max_nfev=500)
        sh, g, t, ng, bs = unpack_a(fit.x)
        w, h, _, _ = scores(rows, sh, g, t, ng, bs)
        print('asym fit:     cycle error %.1f%% of peak, harmonic rms %.2f dB' % (w, h))
        print('shape', np.round(sh, 4).tolist(), '\ngains', np.round(g, 2).tolist(), '\ntrims', np.round(t, 2).tolist(),
              '\nnegScale', np.round(ng, 3).tolist(), '\ndirect' if DIRECT_PER_DRIVE[0] else '\nbias', np.round(bs, 4).tolist())
        out = saved.replace('.json', '_%s.json' % stage)
        json.dump({'shape': sh, 'gains': g, 'trims': t, 'negs': ng, 'biases': bs}, open(out, 'w'))
        print('saved', out)
        return
    lo = [0.005, 0.005, -0.6, 1.0, 0.0, 20.0, 0.5, 0.5] + [-20.0] * n + [-12.0] * n
    hi = [0.5, 0.5, 0.6, 3000.0, 1.0, 20000.0, 30.0, 30.0] + [60.0] * n + [12.0] * n
    start = [min(max(v, l + 1e-6), u - 1e-6) for v, l, u in zip(shape0 + gains0 + trims0, lo, hi)]

    def unpack(p):
        return list(p[:8]), list(p[8:8 + n]), list(p[8 + n:])

    def f(p):
        shape, gains, trims = unpack(p)
        out = []
        for r in rows:
            i = DRIVES.index(r['drive'])
            a, b = residuals(r, shape, gains[i], trims[i])
            out.append(a)
            out.append(b)
        return np.concatenate(out)

    fit = least_squares(f, start, bounds=(lo, hi), x_scale='jac', diff_step=1e-3, max_nfev=400)
    shape, gains, trims = unpack(fit.x)
    w, h, _, _ = scores(rows, shape, gains, trims)
    print('fitted:     cycle error %.1f%% of peak, harmonic rms %.2f dB' % (w, h))
    print('shape', np.round(shape, 4).tolist(), '\ngains', np.round(gains, 2).tolist(), '\ntrims', np.round(trims, 2).tolist())
    json.dump({'shape': shape, 'gains': gains, 'trims': trims}, open(saved, 'w'))
    print('saved', saved)


if __name__ == '__main__':
    main()
