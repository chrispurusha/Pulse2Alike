#!/usr/bin/python3
# One score for a filter saturation candidate (prototype switches in the environment): the noise squash
# (squash_session + squash2_session's resonance set), the self-oscillation's level and pitch against resonance
# 100-127 (squash2), the open oscillator's harmonics.  usage: P2_...=v filter_sat_score.py
import os, shutil, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import squash2_session as s2
import squash_fit

HW = None


def score(env, verbose=False):
    global HW
    if HW is None:
        HW = s2.table('hw', verbose=False)
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp'))
    s2.render_all(dict(os.environ, **env), d)
    p2 = s2.table('p2', d, verbose=False)
    shutil.rmtree(d, ignore_errors=True)
    squash = [p2[k][0] - HW[k][0] for k in HW if k.startswith('r')]
    so = [(12 * np.log2(p2[k][0] / HW[k][0]), p2[k][1] - HW[k][1]) for k in HW if k.startswith('so_') and k != 'so_r97']
    pitch = np.array([a for a, _ in so])
    first = squash_fit.score(int(env.get('P2_LADDER_CURVE', 0)), float(env.get('P2_LADDER_D', 0)),
                             float(env.get('P2_LOOP_D', 3.1)), False, env, quiet=True)
    r = dict(squash1=first['squash'], squash2=float(np.sqrt(np.mean(np.square(squash)))), tone=first['tone'],
             so_level=float(np.mean([b for _, b in so])), so_spread=float(np.std([b for _, b in so])),
             so_shift=float(pitch[-1] - pitch[0]), levels=first['levels'])
    if verbose:
        print('%-60s' % ' '.join('%s=%s' % (k[3:], v) for k, v in env.items()), ' '.join(
            '%s %s' % (k, ('%.2f' % v) if not isinstance(v, list) else '/'.join('%+.1f' % x for x in v)) for k, v in r.items()))
    return r


if __name__ == '__main__':
    score({k: v for k, v in os.environ.items() if k.startswith('P2_')}, True)
