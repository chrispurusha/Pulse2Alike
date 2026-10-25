#!/usr/bin/python3
# NOTE: the P2_SYNC_* / P2_SAW3_SHIFT switches it sets existed only while this was fitted (2026-10-25) and are gone;
# without them it scores the engine as built (p2Plugin notes §22 has the result).
# Scores the prototype sync switches (P2_SYNC_INVERT, P2_SYNC_OFFSET, P2_SAW3_SHIFT) against sync_phase_session's
# takes (circular correlation, sign fixed) and P006's LEVEL2 path (level and harmonic rms, notes 48 and 60).
import itertools, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polarity_session as ps
import sync_phase_session as sp
import p006_level2_check as p6

D = os.environ.get('TMPDIR', '/tmp')
HW = {n: ps.cycle(os.path.join(sp.OUT, 'hw_%s.wav' % n), 1.0) for n in sp.CASES}
P6 = {n: p6.spectrum(os.path.join(p6.OUT, 'hw_n%d.wav' % n), 1.0, n) for n in (48, 60)}


def score(combo):
    inv, off, shift = combo
    env = dict(os.environ, P2_SYNC_OFFSET=str(off), P2_SAW3_SHIFT=str(shift))
    if inv:
        env['P2_SYNC_INVERT'] = '1'
    tag = '%d_%.2f_%.2f' % combo
    corr = {}
    for n, (_, ov) in sp.CASES.items():
        p = os.path.join(D, 'sg_%s_%s.wav' % (tag, n))
        subprocess.run(['./p2render', '-', '48', '2.0', '0.2', p, '192000', *ps.BASE_ENGINE, 'osc3synctoosc2=1', *ov], check=True,
                       capture_output=True, env=env)
        a, e = HW[n], ps.cycle(p, 10.0)
        A, E = (a - a.mean()) / a.std(), (e - e.mean()) / e.std()
        corr[n] = max(np.dot(A, np.roll(E, k)) / len(A) for k in range(256))
    p6r = []
    for note in (48, 60):
        p = os.path.join(D, 'sg_%s_p6_%d.wav' % (tag, note))
        subprocess.run(['./p2render', p6.SYX, str(note), '1.6', '0.3', p, '192000', *p6.OVR], check=True, capture_output=True, env=env)
        (lh, hh), (le, he) = P6[note], p6.spectrum(p, 10.0, note)
        keep = hh > hh.max() - 45
        d = (he - hh) - np.median((he - hh)[keep])
        p6r.append((le - lh, np.sqrt(np.mean(d[keep] ** 2))))
    return combo, corr, p6r


if __name__ == '__main__':
    combos = list(itertools.product((0, 1), [round(0.1 * k, 2) for k in range(10)], (0.0, 0.5)))
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(score, combos))
    rows.sort(key=lambda r: -np.mean(list(r[1].values())))
    print('invert offset sawshift | mean corr | %s | P006 level/harm n48, n60' % ' '.join(n[:5] for n in sp.CASES))
    for (inv, off, sh), corr, p6r in rows[:12]:
        print('  %d     %.1f    %.1f    |  %.3f   | %s | %+5.1f/%.1f  %+5.1f/%.1f' % (inv, off, sh, np.mean(list(corr.values())),
              ' '.join('%.2f ' % corr[n] for n in sp.CASES), p6r[0][0], p6r[0][1], p6r[1][0], p6r[1][1]))
    base = [r for r in rows if r[0] == (0, 0.0, 0.0)][0]
    print('as built: mean corr %.3f, P006 %+.1f/%.1f %+.1f/%.1f' % (np.mean(list(base[1].values())), *base[2][0], *base[2][1]))
