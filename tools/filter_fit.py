#!/usr/bin/python3
# Fits the linear filter model (design §3a) to every EXT sweep at once, magnitude only.
# usage: filter_fit.py <filter capture dir> [--stages]   writes fit.json (fit_stages.json) there, prints residuals per take
import glob, json, os, re, sys

import numpy as np
from scipy.optimize import brentq, least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filter_sweep as fs

GRID = 2 ** np.arange(np.log2(20), np.log2(40000), 1 / 24)
RES = (0, 16, 32, 48, 64, 80, 88, 92, 96)
MODES = ('lp24', 'lp12', 'bp12', 'hp12')
MAX_CUTOFF = 116             # above this the self-oscillation labels are not trusted (findings)
STAGES = '--stages' in sys.argv          # a pole frequency per stage, and LP24 = stage 4 alone


def smoothed(x, y):
    f, H, _ = fs.response(x, y)
    p = np.abs(H) ** 2
    return np.array([10 * np.log10(np.mean(p[(f > c * 2 ** (-1 / 48)) & (f < c * 2 ** (1 / 48))]) + 1e-30) for c in GRID])


def load(d):
    cache = os.path.join(d, 'fit_data.npz')    # delete to re-read the takes
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        return list(z['takes']), z['floor']
    x = fs.sweep()
    floor = smoothed(x, fs.read_wav(os.path.join(d, 'floor_ext0.wav'))[:, 0])
    takes = []
    for p in sorted(glob.glob(os.path.join(d, '*_c*.wav'))):
        m = re.match(r'(lvl45_)?(lp24|lp12|bp12|hp12)_c(\d+)(?:_r(\d+))?\.wav$', os.path.basename(p))
        if m is None:
            continue
        quiet, mode, c, r = bool(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4) or 0)
        if c > MAX_CUTOFF or r not in RES:
            continue
        # notes §3: at -30 dBFS a resonant peak drives the loop into compression; the -45 dBFS take replaces it
        if not quiet and os.path.exists(os.path.join(d, 'lvl45_' + os.path.basename(p))):
            continue
        level = -45.0 if quiet else fs.LEVEL_DB
        takes.append((mode, c, r, smoothed(fs.sweep(level), fs.read_wav(p)[:, 0]), level))
    np.savez(cache, takes=np.array(takes, dtype=object), floor=floor)
    return takes, floor


def selfosc_hz(d):
    a = np.loadtxt(os.path.join(d, 'selfosc_lp24_osc.csv'), delimiter=',')
    return dict(zip(a[:, 0].astype(int), a[:, 1]))


# Parameter vector layout
def unpack(p):
    i = 0
    beta = p[i]; i += 1
    f_loop = p[i]; i += 1
    k = dict(zip(RES, p[i:i + len(RES)])); i += len(RES)
    mix = {}
    for m in MODES:
        mix[m] = p[i:i + 6]; i += 6       # the input, then the loop input and stages 1-4
    sh_a, sh_b, top1, top2 = p[i:i + 4]; i += 4
    ratios = np.concatenate([[1.0], p[i:i + 3]]) if STAGES else np.ones(4)
    return beta, f_loop, k, mix, sh_a, sh_b, top1, top2, ratios


def model_db(p, mode, c, r, fso):
    beta, f_loop, k, mix, sh_a, sh_b, top1, top2, ratios = unpack(p)
    # notes §1: the pole frequency from the measured oscillation frequency through the loop's phase condition
    phase = lambda fp: np.sum(np.arctan(fso / (fp * ratios))) + np.arctan(fso / f_loop) - np.pi
    fp = beta * brentq(phase, fso * 1e-3, fso * 1e3)
    s = 1j * GRID
    Gs = [1 / (1 + s / (fp * q)) for q in ratios]
    L = 1 / (1 + s / f_loop)
    y0 = 1 / (1 + k[r] * L * Gs[0] * Gs[1] * Gs[2] * Gs[3])
    ys = [np.ones_like(y0), y0]
    for G in Gs:
        ys.append(ys[-1] * G)
    w = mix[mode] if not (STAGES and mode == 'lp24') else np.array([0, 0, 0, 0, 0, mix[mode][5]])
    out = sum(w[n] * ys[n] for n in range(6))
    ext = (1 + s / sh_a) / (1 + s / sh_b) / (1 + s / top1) / (1 + s / top2)
    return 20 * np.log10(np.abs(out * ext) + 1e-30)


def initial():
    p = [1.0, 60000.0]
    p += [0, 0.1, 0.78, 1.57, 2.35, 3.12, 3.52, 3.73, 3.9]
    p += [0, 0, 0, 0, 0, 1.7]           # lp24: stage 4
    p += [0, 0, 0, 1.4, 0, 0]           # lp12: stage 2
    p += [0, 0, 1.2, -1.2, 0, 0]        # bp12: stage 1 - stage 2
    p += [0, 0.35, -0.7, 0.35, 0, 0]    # hp12: (1 - G)^2
    p += [400.0, 250.0, 15000.0, 40000.0]
    if STAGES:
        p += [1.0, 1.0, 1.0]
    return np.array(p, dtype=float)


def main():
    d = [a for a in sys.argv[1:] if not a.startswith('--')][0]
    takes, floor = load(d)
    so = selfosc_hz(d)
    # notes §2: the floor was measured in one mode only; a take's own dynamic range bounds it as well
    # a quieter sweep raises the floor, as measured relative to what was played, by the difference
    masks = [(t[3] > floor + (fs.LEVEL_DB - t[4]) + 10) & (t[3] > t[3].max() - 45) for t in takes]

    def resid(p):
        out = []
        for (mode, c, r, db, _), m in zip(takes, masks):
            out.append((model_db(p, mode, c, r, so[c]) - db)[m])
        return np.concatenate(out)

    p0 = initial()
    lo = np.full_like(p0, -np.inf); hi = np.full_like(p0, np.inf)
    lo[0], hi[0] = 0.5, 2.0
    lo[1], hi[1] = 2000, 1e6
    lo[2:11] = -0.5; hi[2:11] = 4.5
    n_ext = len(p0) - 4 - (3 if STAGES else 0)
    lo[n_ext:n_ext + 4] = 10; hi[n_ext:n_ext + 4] = 1e6
    if STAGES:
        lo[-3:] = 0.3; hi[-3:] = 3.0
    fit = least_squares(resid, p0, bounds=(lo, hi), x_scale='jac', max_nfev=4000)
    p = fit.x
    beta, f_loop, k, mix, sh_a, sh_b, top1, top2, ratios = unpack(p)
    r = resid(p)
    print('stage pole ratios:', ' '.join('%.3f' % q for q in ratios))
    print('rms %.2f dB over %d points, max %.1f' % (np.sqrt(np.mean(r ** 2)), len(r), np.abs(r).max()))
    print('beta %.4f  loop pole %.0f Hz  shelf zero %.0f pole %.0f Hz (bass +%.1f dB)  top poles %.0f %.0f Hz' % (
        beta, f_loop, sh_a, sh_b, 20 * np.log10(sh_a / sh_b) * -1 if False else 20 * np.log10(sh_b / sh_a) * -1, top1, top2))
    print('k by resonance:', ' '.join('%d:%.3f' % (rv, k[rv]) for rv in RES))
    for m in MODES:
        print('mix %-5s' % m, ' '.join('%+.3f' % v for v in mix[m]))
    print('per take rms dB:')
    line = []
    for (mode, c, rr, db, _), msk in zip(takes, masks):
        e = (model_db(p, mode, c, rr, so[c]) - db)[msk]
        line.append('%s_c%d_r%d %.2f' % (mode, c, rr, np.sqrt(np.mean(e ** 2))))
    print('  ' + ' | '.join(line))
    json.dump({'params': list(p), 'res': RES, 'modes': MODES, 'stages': STAGES},
              open(os.path.join(d, 'fit_stages.json' if STAGES else 'fit.json'), 'w'), indent=1)


main()
