#!/usr/bin/python3
# NOTE: the P2_* switches it sets lived in p2Filter.c only while the 2026-10-24 refit was explored, and are gone;
# without them this scores the engine as built (p2Filter notes §9 has the result).
# Scores the engine's noise squash against squash_session's instrument takes, for filter saturation settings given
# in the environment (P2_LADDER_D, P2_LOOP_D, P2_LADDER_CURVE - the prototype switches); with the self-oscillation's
# level and pitch (selfosc_level_session) and the triangle's harmonics.  usage: squash_fit.py curve ladderD loopD [...]
import os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash_session as sq
import selfosc_level_session as so
from osc_analyse import read

TAGS = ('c127_v40', 'c64_v40', 'c40_v40', 'c64_r41_v40')
RENDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')


def settings():
    for tag in TAGS:
        cutoff, res, vol = sq.SETTINGS[tag]
        for level in sq.LEVELS:
            yield tag, cutoff, res, vol, level, sq.NOISE
        yield tag, cutoff, res, vol, 127, 0


def render(env, out, tag, cutoff, res, vol, level, noise):
    path = os.path.join(out, '%s_o%d_n%d.wav' % (tag, level, noise))
    subprocess.run([RENDER, '-', str(sq.NOTE), str(sq.HOLD), '0.3', path, '192000', *sq.ENGINE_BASE,
                    'osc1level=%d' % level, 'noiselevel=%d' % noise, 'cutoff=%d' % cutoff, 'resonance=%d' % res,
                    'volume=%d' % vol], check=True, capture_output=True, env=env)
    return path


def fundamental(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.4 * r):on + int(2.2 * r)]
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    return [20 * np.log10(abs(np.sum(s * w * np.exp(-2j * np.pi * sq.F0 * k * t))) * 2 / w.sum()) for k in (1, 3, 5)]


def harmonics(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.4 * r):on + int(2.2 * r)]
    t = np.arange(len(s)) / r
    w = np.hanning(len(s))
    h = np.array([20 * np.log10(abs(np.sum(s * w * np.exp(-2j * np.pi * sq.F0 * k * t))) * 2 / w.sum()) for k in range(1, 10)])
    return h - h[0], h[0]


def score(curve, ladder, loop, verbose, extra=None, quiet=False):
    env = dict(os.environ, P2_LADDER_D=str(ladder), P2_LOOP_D=str(loop), P2_LADDER_CURVE=str(curve))
    env.update(extra or {})
    out = tempfile.mkdtemp(prefix='sqfit_', dir=os.environ.get('TMPDIR', '/tmp'))
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda a: render(env, out, *a), settings()))
    errs = []
    for tag in TAGS:
        hw = lambda lv, nz: sq.between_harmonics(os.path.join(sq.OUT, 'hw_%s_o%d_n%d.wav' % (tag, lv, nz)))[0]
        p2 = lambda lv, nz: sq.between_harmonics(os.path.join(out, '%s_o%d_n%d.wav' % (tag, lv, nz)))[0]
        hwRef, p2Ref = hw(0, sq.NOISE), p2(0, sq.NOISE)
        valid = (hw(127, 0) - hwRef < -10) & (hwRef > -80)
        rows = []
        for level in sq.LEVELS[1:]:
            dh, dp = hw(level, sq.NOISE) - hwRef, p2(level, sq.NOISE) - p2Ref
            errs += list((dp - dh)[valid])
            rows.append((level, dh, dp))
        if verbose:
            print('  %s  (bands %s valid)' % (tag, ''.join('x' if v else '.' for v in valid)))
            for level, dh, dp in rows:
                print('    osc %3d  hw %s | p2 %s' % (level, ' '.join('%5.1f' % v for v in dh), ' '.join('%5.1f' % v for v in dp)))
    tone, levels = [], []
    for tag in TAGS:
        hh, h1h = harmonics(os.path.join(sq.OUT, 'hw_%s_o127_n0.wav' % tag))
        hp, h1p = harmonics(os.path.join(out, '%s_o127_n0.wav' % tag))
        keep = hh > -60
        tone += list((hp - hh)[keep][1:])
        levels.append(h1p + 20 - h1h)
    selfosc = {}
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda cr: so.render(os.path.join(out, 'so_c%d_r%d.wav' % cr), cr[0], cr[1], env), so.CASES))
    for cutoff, res in so.CASES:
        p = os.path.join(out, 'so_c%d_r%d.wav' % (cutoff, res))
        fh, lh, _ = so.measure(os.path.join(so.OUT, 'hw_c%d_r%d.wav' % (cutoff, res)))
        fp, lp, _ = so.measure(p, 2.0)
        selfosc[(cutoff, res)] = (12 * np.log2(fp / fh), lp + 20 - lh)
    shift = np.mean([selfosc[(c, 127)][0] - selfosc[(c, 100)][0] for c in (40, 64, 88)]) - 0.0
    result = dict(squash=np.sqrt(np.mean(np.square(errs))), tone=np.sqrt(np.mean(np.square(tone))),
                  so127=np.mean([selfosc[(c, 127)][1] for c in (40, 64, 88)]), so100=np.mean([selfosc[(c, 100)][1] for c in (40, 64, 88)]),
                  shift=shift, levels=levels)
    shutil.rmtree(out, ignore_errors=True)
    if quiet:
        return result
    print('curve %d ladder D %5.2f loop D %.2f: squash rms %.2f (mean %+.2f) | tone rms %.2f (mean %+.2f) | h1 level %s | '
          'self-osc level r127 %+.1f r100 %+.1f dB, pitch r127-r100 engine-hw %+.2f st, r127 %+.2f st' %
          (curve, ladder, loop, np.sqrt(np.mean(np.square(errs))), np.mean(errs), np.sqrt(np.mean(np.square(tone))), np.mean(tone),
           ' '.join('%+.1f' % v for v in levels), np.mean([selfosc[(c, 127)][1] for c in (40, 64, 88)]),
           np.mean([selfosc[(c, 100)][1] for c in (40, 64, 88)]), shift, np.mean([selfosc[(c, 127)][0] for c in (40, 64, 88)])))


if __name__ == '__main__':
    args = [float(a) for a in sys.argv[1:]]
    for i in range(0, len(args), 3):
        score(int(args[i]), args[i + 1], args[i + 2], len(args) == 3)

