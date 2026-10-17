#!/usr/bin/python3
# The filter-envelope session (todo, Filter): the self-oscillating filter turns the cutoff into a pitch, so the
# envelope's amount, keytrack and trigger behaviour can be read off the oscillation's frequency.
# usage: fenv_session.py <outdir> amount|keytrack|times|trigger
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from mod_step import cycle_track

RATE = 192000
OSC_HZ_AT_ZERO, STEPS_PER_OCT = 23.93, 11.977       # the measured cutoff law (design §3a)


def cutoff_steps(hz):
    return STEPS_PER_OCT * np.log2(hz / OSC_HZ_AT_ZERO)


def take(outdir, tag, sound, items, seconds):
    p2rig.set_sound(dict(osc1_level=0, resonance=127, volume=40, **sound))
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*items)
    cap.communicate()
    json.dump({'sound': sound}, open(path[:-4] + '.json', 'w'))
    return path


def steady_steps(path, t0, t1):
    t, f = cycle_track(path)
    m = (t > t0) & (t < t1) & (f > 15) & (f < 30000)
    return float(np.median(cutoff_steps(f[m]))) if m.any() else float('nan')


def first_sound(path):
    t, f = cycle_track(path)
    ok = (f > 15) & (f < 30000)
    return t[ok][0] if ok.any() else 0.0


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    hold = dict(enva_a=0, enva_s=127, envf_a=0, envf_d=0, envf_s=127, envf_r=0)
    if what == 'amount':
        print('filter env amount -> cutoff steps added (base cutoff 40, env held at full)')
        for a in list(range(0, 128, 8)) + [127]:
            p = take(outdir, 'amount_%d' % a, dict(cutoff=40, vcf_env=a, **hold), p2rig.note_items(60, 1.5), 1.5)
            s0 = first_sound(p)
            print('  %3d %+7.2f' % (a, steady_steps(p, s0 + 0.5, s0 + 1.4) - 40.0))
    elif what == 'keytrack':
        print('keytrack 127 (base cutoff 40, env amount 0): note -> cutoff steps added')
        for n in (24, 36, 48, 60, 72, 84, 96):
            p = take(outdir, 'keytrack_n%d' % n, dict(cutoff=40, vcf_env=64, vcf_keytrack=127, **hold), p2rig.note_items(n, 1.2), 1.2)
            s0 = first_sound(p)
            print('  %3d %+7.2f' % (n, steady_steps(p, s0 + 0.4, s0 + 1.1) - 40.0))
    elif what == 'times':
        print('filter env (amount 127, base 20): cutoff steps against time')
        for stage, v in (('decay', 64), ('decay', 80), ('attack', 64), ('attack', 80)):
            env = dict(enva_a=0, enva_s=127, envf_a=0, envf_d=0, envf_s=127, envf_r=0)
            if stage == 'decay':
                env.update(envf_d=v, envf_s=0)
            else:
                env['envf_a'] = v
            p = take(outdir, 'times_%s_%d' % (stage, v), dict(cutoff=20, vcf_env=127, **env), p2rig.note_items(60, 6.0), 6.0)
            t, f = cycle_track(p)
            ok = (f > 15) & (f < 30000)
            t, st = t[ok], cutoff_steps(f[ok])
            s0 = t[0]
            print('  %s %d:' % (stage, v), ' '.join('%gs:%.1f' % (dt, np.interp(s0 + dt, t, st)) for dt in (0.0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 5.5)))
    elif what == 'trigger':
        print('trigger modes: note 60, then note 72 overlapping at 1.0 s; decay 80, amount 127, base 20')
        ch = p2rig.CHANNEL - 1
        items = [p2rig.hexmsg(0x90 | ch, 60, 100), 'sleep:1000', p2rig.hexmsg(0x90 | ch, 72, 100), 'sleep:2000',
                 p2rig.hexmsg(0x80 | ch, 72, 0), p2rig.hexmsg(0x80 | ch, 60, 0)]
        names = ['SNG1', 'SNG2', 'RET1', 'RET2', 'RET3']
        for m in range(5):
            env = dict(enva_a=0, enva_s=127, envf_a=0, envf_d=80, envf_s=0, envf_r=0, envf_trigger=m)
            p = take(outdir, 'trigger_%s' % names[m], dict(cutoff=20, vcf_env=127, **env), items, 3.0)
            t, f = cycle_track(p)
            ok = (f > 15) & (f < 30000)
            t, st = t[ok], cutoff_steps(f[ok])
            s0 = t[0]
            print('  %s:' % names[m], ' '.join('%gs:%.1f' % (dt, np.interp(s0 + dt, t, st)) for dt in (0.0, 0.5, 0.95, 1.02, 1.1, 1.5, 2.5)))


if __name__ == '__main__':
    main()
