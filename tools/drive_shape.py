#!/usr/bin/python3
# Fits the drive curve's shape (tools/drive_model.c, as in src/p2Drive.c) to drive_sweep/ by harmonic spectra: the
# model runs on each NONE take and its harmonics 1-15 are scored against the instrument's take at the same osc level,
# note and Drive. Stage "shape" fits the curve on inputs above the quiet-input knee with that loss off; stage "loss"
# then fits the loss's knee, slope and trim per Drive to every level, with the shape held. p2Drive notes §6.
# The EXT IN sines at 100 Hz-3 kHz (192k/drive/) are fitted too; stage "sines" lists them beside the old shape.
# usage: drive_shape.py <curve 1=TUBE 2=FUZZ> [shape|loss|score|sines] [shape.json]
import ctypes, json, os, subprocess, sys, tempfile

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from osc_analyse import read
from drive_level import name, onset, rms_window, db, SHAPES, LOSS, DRIVE_AT, SWEEP, WINDOW

DRIVES = (0, 16, 32, 64, 127)
HARMONICS = 15
FLOOR_DB = -65.0           # harmonics further below the instrument's fundamental are its noise, not its curve
STATIC_FROM_DB = -29.5     # inputs above the quiet-input knee: the shape alone
PRE_S = 0.1                # the model starts this far ahead of the onset, so its couplings settle as the note's do

DP = ctypes.POINTER(ctypes.c_double)
SINES = '/Volumes/ext-ssd/Captures/Pulse2/192k/drive/'
SINE_LEVELS = (-30, -20, -10)   # the EXT IN steps, HOLD s each (tools/vol_check.py)
SINE_HOLD_S = 2.0


def build():
    lib = os.path.join(tempfile.gettempdir(), 'p2_drive_model.dylib')
    subprocess.check_call(['clang', '-O2', '-shared', '-o', lib, os.path.join(HERE, 'drive_model.c')])
    return ctypes.CDLL(lib)


LIB = build()


def run(x, rate, shape, gain, loss):
    x = np.ascontiguousarray(x, dtype=np.float64)
    out = np.empty_like(x)
    sh = np.ascontiguousarray(shape, dtype=np.float64)
    ls = np.ascontiguousarray(loss, dtype=np.float64)
    LIB.drive_run(x.ctypes.data_as(DP), len(x), ctypes.c_double(rate), sh.ctypes.data_as(DP), ctypes.c_double(gain),
                  ls.ctypes.data_as(DP), out.ctypes.data_as(DP))
    return out


def fundamental(s, rate):
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    f = np.fft.rfftfreq(len(s), 1 / rate)
    i = np.argmax(sp[(f > 40) & (f < 2000)]) + np.flatnonzero(f > 40)[0]
    a, b, c = np.log(sp[i - 1:i + 2] + 1e-30)
    return f[i] + (0.5 * (a - c) / (a - 2 * b + c)) * (f[1] - f[0])


def harmonics(s, rate, f0):
    w = s - np.mean(s)
    sp = np.abs(np.fft.rfft(w * np.hanning(len(w)))) * 2 / np.sum(np.hanning(len(w)))
    bin_hz = rate / len(w)
    return np.array([db(sp[max(0, int(round(k * f0 / bin_hz)) - 2):int(round(k * f0 / bin_hz)) + 3].max())
                     for k in range(1, HARMONICS + 1)])


# Every take of one curve: (drive, input dB, the NONE take's span from PRE_S before its onset, the instrument's
# harmonics, f0, rate)
def load(curve):
    takes = []

    for note in (48, 72, 84):
        prefix = '' if note == 48 else 'n%d_' % note
        levels = sorted({int(f[len(prefix):].split('_')[0][1:]) for f in os.listdir(SWEEP)
                         if f.endswith('_c0_d0.wav') and (f.startswith(prefix + 'l') if prefix else f.startswith('l'))})

        for level in levels:
            if level <= 12:
                continue                                    # below the oscillator's level law: no input
            none, rate = read(name(level, 0, 0, note))
            x = none[:, 0]
            at = onset(x, rate)
            a, b = int(WINDOW[0] * rate), int(WINDOW[1] * rate)
            f0 = fundamental(x[at + a:at + b], rate)

            for d in DRIVES:
                path = name(level, curve, d, note)

                if not os.path.exists(path):
                    continue
                hw, _ = read(path)
                h = hw[:, 0]
                ah = onset(h, rate)
                pre = int(PRE_S * rate)
                takes.append((d, db(rms_window(x, rate, at)), note, x[at - pre:at + b],
                              harmonics(h[ah + a:ah + b], rate, f0), f0, rate, pre + a, pre + b))
    return takes


# The EXT IN sines as takes too (label 'sine'): the model runs over the whole NONE take, scored on each step's window
def load_sines(curve):
    word = {1: 'TUBE', 2: 'FUZZ'}[curve]
    takes = []

    for hz in (100, 300, 1000, 3000):
        none, rate = read(SINES + 'drive_NONE_0_f%d.wav' % hz)
        x = none[:, 0]

        for d in (0, 32, 64, 127):
            path = SINES + 'drive_%s_%d_f%d.wav' % (word, d, hz)

            if not os.path.exists(path):
                continue
            hw, _ = read(path)
            h = hw[:, 0]

            for (a, b), (ha, hb) in zip(sine_steps(x, rate), sine_steps(h, rate)):
                takes.append((d, db(np.std(x[a:b])), 'sine', x[:b], harmonics(h[ha:hb], rate, hz), float(hz), rate, a, b))
    return takes


# The shape at one Drive: TUBE's bias moves with Drive (p2Drive notes §3), so a fit may carry one per Drive
def shape_at(shape, biases, d):
    s = list(shape)

    if biases is not None:
        s[2] = biases[DRIVES.index(d)]
    return s


def model_harmonics(t, shape, gain_db, loss):
    d, _, _, span, _, f0, rate, a, b = t
    return harmonics(run(span, rate, shape, 10 ** (gain_db / 20), loss)[a:b], rate, f0)


def residual(t, mh):
    hh = t[4]
    keep = hh - hh[0] > FLOOR_DB
    w = np.ones(HARMONICS)
    w[0] = 3.0                                              # the level
    return ((mh - hh) * w)[keep]


def score(takes, shape, gains, losses, biases=None):
    rows = {}

    for t in takes:
        i = DRIVES.index(t[0])
        r = residual(t, model_harmonics(t, shape_at(shape, biases, t[0]), gains[i], losses[i]))
        rows.setdefault((t[2], t[0]), []).append(np.sqrt(np.mean(r ** 2)))
    return rows


def report(title, rows):
    print(title)

    for (note, d), v in sorted(rows.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        print('  note %s drive %3d: harmonic rms %.1f dB over %d levels' % (note, d, np.mean(v), len(v)))
    print('  all: %.2f dB' % np.mean([x for v in rows.values() for x in v]), flush=True)


def sine_steps(s, rate):
    env = np.sqrt(np.convolve(s ** 2, np.ones(rate // 100) / (rate // 100), 'same'))
    start = np.flatnonzero(env > 10 ** (-60 / 20))[0]
    return [(start + int((i * SINE_HOLD_S + 0.6) * rate), start + int((i * SINE_HOLD_S + 1.4) * rate))
            for i in range(len(SINE_LEVELS))]


# The model on each NONE sine take against the instrument's take, per frequency and Drive: harmonic rms in dB
def sines(curve, fits):
    word = {1: 'TUBE', 2: 'FUZZ'}[curve]
    print('EXT IN sines (unfitted): harmonic rms dB per input level %s, for %s' % (SINE_LEVELS, ', '.join(fits)))

    for hz in (100, 300, 1000, 3000):
        none, rate = read(SINES + 'drive_NONE_0_f%d.wav' % hz)
        x = none[:, 0]
        nsteps = sine_steps(x, rate)

        for d in (0, 32, 64, 127):
            path = SINES + 'drive_%s_%d_f%d.wav' % (word, d, hz)

            if not os.path.exists(path):
                continue
            hw, _ = read(path)
            h = hw[:, 0]
            row = '  %4d Hz drive %3d:' % (hz, d)

            for label, (shape_of, gain_at, loss_at) in fits.items():
                y = run(x, rate, shape_of(d), 10 ** (gain_at(d) / 20), loss_at(d))
                errs = []

                for (a, b), (ha, hb) in zip(nsteps, sine_steps(h, rate)):
                    hh = harmonics(h[ha:hb], rate, hz)
                    keep = hh - hh[0] > FLOOR_DB
                    w = np.ones(HARMONICS)
                    w[0] = 3.0
                    errs.append(np.sqrt(np.mean((((harmonics(y[a:b], rate, hz) - hh) * w)[keep]) ** 2)))
                row += '  %s %s' % (label, ' '.join('%5.1f' % e for e in errs))
            print(row, flush=True)


def main():
    curve = int(sys.argv[1])
    stage = sys.argv[2] if len(sys.argv) > 2 else 'shape'
    saved = sys.argv[3] if len(sys.argv) > 3 else os.path.join(tempfile.gettempdir(), 'p2_drive_shape_%d.json' % curve)
    takes = load(curve) if stage != "sines" else []
    base = list(SHAPES[curve][:6]) + [2.5, 2.5]
    gains = [float(np.interp(d, DRIVE_AT, SHAPES[curve][6])) for d in DRIVES]
    old_loss = [[float(np.interp(d, DRIVE_AT, v)) for v in LOSS[curve]] for d in DRIVES]
    old_loss = [[k, s, t] for k, s, t in old_loss]

    if stage == 'sines':
        state = json.load(open(saved))
        tanh_like = list(SHAPES[curve][:6]) + [2.5, 2.5]
        old = (lambda d: tanh_like, lambda d: float(np.interp(d, DRIVE_AT, SHAPES[curve][6])),
               lambda d: [float(np.interp(d, DRIVE_AT, v)) for v in LOSS[curve]])
        bias = state.get('bias')
        new = (lambda d: shape_at(state['shape'], [float(np.interp(d, DRIVES, bias))] * len(DRIVES) if bias else None, DRIVES[0]),
               lambda d: float(np.interp(d, DRIVES, state['gains'])),
               lambda d: [float(np.interp(d, DRIVES, [l[i] for l in state['loss']])) for i in range(3)])
        sines(curve, {'old': old, 'new': new})
        return

    if stage == 'score':
        state = json.load(open(saved))
        report('saved fit', score(takes, state['shape'], state['gains'], state['loss'], state.get('bias')))
        return

    if stage == 'shape':
        static = [t for t in takes if t[1] >= STATIC_FROM_DB] + [t for t in load_sines(curve) if t[1] >= -25.0]
        off = [[0.0, 0.0, 0.0]] * len(DRIVES)
        report('before (the engine\'s shape, a tanh-like knee)', score(static, base, gains, off))
        lo = [0.005, 0.005, -0.5, 1.0, 0.0, 20.0, 0.5, 0.5] + [-20.0] * len(DRIVES)
        hi = [0.5, 0.5, 0.5, 3000.0, 1.0, 20000.0, 30.0, 30.0] + [50.0] * len(DRIVES)

        # FUZZ: one knee hardness for both sides - a free pair turned lopsided to copy the even harmonics the sweep's
        # triangle brings in. Its ceilings and bias stay free: forced equal and zero, the fit lost 4 dB everywhere
        symmetric = curve == 2

        per_drive_bias = curve == 1
        n = len(DRIVES)

        def unpack(p):
            q = list(p)

            if symmetric:
                q.insert(7, q[6])           # one hardness
            biases = q[8 + n:] if per_drive_bias else None
            return q[:8], q[8:8 + n], biases

        def f(p):
            shape, g, biases = unpack(p)
            return np.concatenate([residual(t, model_harmonics(t, shape_at(shape, biases, t[0]), g[DRIVES.index(t[0])],
                                                               [0.0, 0.0, 0.0])) for t in static])
        start, lo, hi = base + gains, lo, hi

        if per_drive_bias:
            start, lo, hi = start + [base[2]] * n, lo + [-1.0] * n, hi + [1.0] * n

        if symmetric:
            del start[7], lo[7], hi[7]
        fit = least_squares(f, start, bounds=(lo, hi), x_scale='jac', diff_step=1e-3, max_nfev=400)
        shape, gains, biases = unpack(fit.x)
        report('after', score(static, shape, gains, off, biases))
        json.dump({'shape': shape, 'gains': gains, 'loss': old_loss, 'bias': biases}, open(saved, 'w'))
        print('shape', np.round(shape, 4).tolist(), '\ngains', np.round(gains, 2).tolist(),
              '\nbias', None if biases is None else np.round(biases, 4).tolist(), '\nsaved', saved)
        return

    state = json.load(open(saved))
    shape, gains, losses, biases = state['shape'], state['gains'], [], state.get('bias')
    n48 = [t for t in takes if t[2] == 48] + load_sines(curve)

    for i, d in enumerate(DRIVES):
        mine = [t for t in n48 if t[0] == d]

        def f(p, mine=mine, i=i):
            return np.concatenate([residual(t, model_harmonics(t, shape_at(shape, biases, d), gains[i], p)) for t in mine])
        fit = least_squares(f, old_loss[i], bounds=([-45.0, 0.0, -6.0], [-20.0, 8.0, 6.0]), diff_step=1e-3)
        losses.append(list(fit.x))
        print('drive %3d: knee %.2f slope %.2f trim %+.2f' % (d, *fit.x), flush=True)
    state['loss'] = losses
    json.dump(state, open(saved, 'w'))
    report('every level, shape and loss', score(takes, shape, gains, losses, biases))


if __name__ == '__main__':
    main()
