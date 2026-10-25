#!/usr/bin/python3
# Under sync, where osc 2's cycle sits against osc 3's: osc 2 synced at osc 3's pitch (note 48), osc 3 audible as the
# reference where noted. One cycle folded, instrument against engine (circular best match, either sign reported).
# usage: sync_phase_session.py [p2render ...]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import polarity_session as ps

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/sync_phase'
CASES = {
    'A_pw40_alone':   (dict(osc2_shape=0, osc2_pw=40, osc2_level=127, osc3_shape=0, osc3_level=0),
                       ['osc2shape=0', 'osc2pulsewidth=40', 'osc2level=127', 'osc3shape=0', 'osc3level=0']),
    'B_pw40_o3saw':   (dict(osc2_shape=0, osc2_pw=40, osc2_level=127, osc3_shape=1, osc3_level=127),
                       ['osc2shape=0', 'osc2pulsewidth=40', 'osc2level=127', 'osc3shape=1', 'osc3level=127']),
    'C_pw40_o3sqr':   (dict(osc2_shape=0, osc2_pw=40, osc2_level=127, osc3_shape=0, osc3_level=60),
                       ['osc2shape=0', 'osc2pulsewidth=40', 'osc2level=127', 'osc3shape=0', 'osc3level=60']),
    'E_saw_o3saw':    (dict(osc2_shape=1, osc2_level=127, osc3_shape=1, osc3_level=60),
                       ['osc2shape=1', 'osc2level=127', 'osc3shape=1', 'osc3level=60']),
    'F_pw100_o3saw':  (dict(osc2_shape=0, osc2_pw=100, osc2_level=127, osc3_shape=1, osc3_level=60),
                       ['osc2shape=0', 'osc2pulsewidth=100', 'osc2level=127', 'osc3shape=1', 'osc3level=60']),
    'G_saw_alone':    (dict(osc2_shape=1, osc2_level=127, osc3_shape=0, osc3_level=0),
                       ['osc2shape=1', 'osc2level=127', 'osc3shape=0', 'osc3level=0']),
}
CH = ' .:-=+*#%@'


def show(v):
    v = (v - v.mean()) / (v.std() + 1e-12)
    return ''.join(CH[min(9, int((x - v.min()) / (np.ptp(v) + 1e-12) * 9.99))] for x in v[::4])


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, (cc, ov) in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(osc1_level=0, noise=0, cutoff=127, volume=40, osc3_sync=1, **cc))
            time.sleep(0.3)
            cap = p2rig.capture(hw, 3.0, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(48, 2.0))
            cap.communicate()
        a = ps.cycle(hw, 1.0)
        A = (a - a.mean()) / a.std()
        j = int(np.argmax(np.abs(np.diff(A, append=A[0]))))     # the biggest step at the left
        A = np.roll(A, -j - 1)
        print('%-14s hw  |%s|' % (name, show(A)))
        for b in sys.argv[1:]:
            p = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'sp.wav')
            subprocess.run([b, '-', '48', '2.0', '0.2', p, '192000', *ps.BASE_ENGINE, 'osc3synctoosc2=1', *ov], check=True, capture_output=True)
            e = ps.cycle(p, 10.0)
            E = (e - e.mean()) / e.std()
            res = {s: max(range(256), key=lambda k: np.dot(A, np.roll(s * E, k))) for s in (1, -1)}
            cs = {s: np.dot(A, np.roll(s * E, res[s])) / len(A) for s in (1, -1)}
            s = max(cs, key=cs.get)
            print('%-14s %-3s |%s|  same %.3f inverted %.3f' % ('', os.path.basename(b)[:3], show(np.roll(s * E, res[s])), cs[1], cs[-1]))
