#!/usr/bin/python3
# squash_session's second round: (1) LEVEL2 - osc 2 with osc 3 on LEVEL2, does osc 3 add squash, and how loud does it
# make osc 2; (2) resonance - the squash at cutoff 64 against resonance, and the self-oscillation's level from 97 up.
# The test sound throughout (p2rig), note 48; the noise read between its harmonics.  usage: squash2_session.py [analyse]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
import selfosc_level_session as so

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/squash2'
TITLES = dict(osc1_shape='osc1shape', osc1_level='osc1level', osc2_shape='osc2shape', osc2_level='osc2level',
              osc3_shape='osc3shape', osc3_routing='osc3routing', osc3_level='osc3level', noise='noiselevel',
              cutoff='cutoff', resonance='resonance', volume='volume', vcf_type='filtertype')
BASE = dict(cutoff=127, resonance=0, volume=40, noise=0, osc1_level=0)


def l2(o3, nz):
    return dict(osc2_shape=1, osc2_level=101, osc3_shape=1, osc3_routing=1, osc3_semi=76, osc3_level=o3, noise=nz)


def reso(lv, res, nz):
    return dict(osc1_shape=2, osc1_level=lv, cutoff=64, resonance=res, noise=nz)


CASES = {'l2_noise': dict(noise=104)}
for o3 in (0, 30, 58, 90, 127):
    CASES['l2_o%d' % o3] = l2(o3, 104)
    CASES['l2_o%d_nn' % o3] = l2(o3, 0)
    CASES['l2_o%d_ref' % o3] = dict(l2(o3, 104), osc2_level=0)   # the routing's own effect on the noise
for res in (0, 41, 60, 80, 92):
    CASES['r%d_noise' % res] = reso(0, res, 104)
    for lv in (90, 127):
        CASES['r%d_o%d' % (res, lv)] = reso(lv, res, 104)
    CASES['r%d_o127_nn' % res] = reso(127, res, 0)
for res in (0, 41, 60, 80, 92):          # LP12, P006's mode
    CASES['lp12_r%d_noise' % res] = dict(reso(0, res, 104), vcf_type=1)
for res in (0, 41):
    CASES['lp12_r%d_o127' % res] = dict(reso(127, res, 104), vcf_type=1)
    CASES['lp12_r%d_o127_nn' % res] = dict(reso(127, res, 0), vcf_type=1)
    CASES['lp12_c40_r%d_noise' % res] = dict(reso(0, res, 104), vcf_type=1, cutoff=40)
    CASES['lp12_c40_r%d_o127' % res] = dict(reso(127, res, 104), vcf_type=1, cutoff=40)
SELFOSC = (97, 100, 104, 110, 118, 127)


def engine_args(settings):
    args = []
    for k, v in settings.items():
        if k == 'osc3_semi':
            args.append('osc3semitone=%d' % (v - 64))
        else:
            args.append('%s=%d' % (TITLES[k], v))
    return args


def render(name, settings, env=None, out=OUT):
    s = dict(BASE, **settings)
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', str(sq.NOTE), str(sq.HOLD), '0.3',
                    os.path.join(out, 'p2_%s.wav' % name), '192000', *sq.ENGINE_BASE, *engine_args(s)],
                   check=True, capture_output=True, env=env)


def capture():
    os.makedirs(OUT, exist_ok=True)
    for name, settings in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(BASE, **settings))
        time.sleep(0.3)
        cap = p2rig.capture(hw, sq.HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(sq.NOTE, sq.HOLD))
        cap.communicate()
    for res in SELFOSC:
        hw = os.path.join(OUT, 'hw_so_r%d.wav' % res)
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(osc1_level=0, noise=0, cutoff=64, resonance=res, volume=40))
        time.sleep(1.0)
        cap = p2rig.capture(hw, so.HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(so.NOTE, so.HOLD))
        cap.communicate()


def table(side, out=OUT, verbose=True):
    """The squash per case and the osc's own harmonic level, the self-oscillation levels; returns them for a fit."""
    g = 20 if side == 'p2' else 0
    bh = lambda n: sq.between_harmonics(os.path.join(out, '%s_%s.wav' % (side, n)))[0]
    res = {}
    for o3 in (0, 30, 58, 90, 127):
        ref = bh('l2_o%d_ref' % o3)
        x2, r = so.read(os.path.join(out, '%s_l2_o%d_nn.wav' % (side, o3)))
        x = x2[:, 0] if x2.ndim > 1 else x2
        on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
        rms = 20 * np.log10(np.sqrt(np.mean(x[on + int(0.4 * r):on + int(2.2 * r)] ** 2))) + g
        res['l2_o%d' % o3] = (bh('l2_o%d' % o3) - ref, rms)
    for rs in (0, 41, 60, 80, 92):
        ref = bh('r%d_noise' % rs)
        for lv in (90, 127):
            res['r%d_o%d' % (rs, lv)] = (bh('r%d_o%d' % (rs, lv)) - ref, None)
    for rs in SELFOSC:
        f, lv, _ = so.measure(os.path.join(out, '%s_so_r%d.wav' % (side, rs)), 2.0 if side == 'p2' else 0.0)
        res['so_r%d' % rs] = (f, lv + g)
    if verbose:
        for k, (a, b) in res.items():
            if k.startswith('so_'):
                print('  %s %-10s %7.1f Hz %6.1f dBFS' % (side, k, a, b))
            else:
                print('  %s %-10s %s%s' % (side, k, ' '.join('%5.1f' % v for v in a), '' if b is None else '   osc2 out %.1f dBFS' % b))
    return res


def render_all(env=None, out=OUT):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda kv: render(kv[0], kv[1], env, out), CASES.items()))
        list(ex.map(lambda rs: so.render(os.path.join(out, 'p2_so_r%d.wav' % rs), 64, rs, env), SELFOSC))


if __name__ == '__main__':
    if 'analyse' not in sys.argv:
        capture()
    render_all()
    print('bands %s' % ' '.join('%d-%d' % b for b in sq.BANDS))
    table('hw')
    table('p2')
