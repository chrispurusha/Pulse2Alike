#!/usr/bin/python3
# The symmetric shapes' polarity, which a fold alone cannot tell from a half-cycle shift: sync gives a reference.
# Osc 2's triangle synced (+7) against its restart; osc 3's square and triangle audible beside a synced osc 2 saw
# (whose polarity is known). Folded on osc 3's period, instrument against engine, either sign.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import polarity_session as ps

CASES = {
    'sync_o2tri': (dict(osc2_shape=2, osc2_level=127, osc2_semi=71, osc3_sync=1),
                   ['osc2shape=2', 'osc2level=127', 'osc2semitone=7', 'osc3synctoosc2=1']),
    'sync_o2saw_o3sqr': (dict(osc2_shape=1, osc2_level=127, osc2_semi=71, osc3_sync=1, osc3_shape=0, osc3_level=127),
                         ['osc2shape=1', 'osc2level=127', 'osc2semitone=7', 'osc3synctoosc2=1', 'osc3shape=0', 'osc3level=127']),
    'sync_o2saw_o3tri': (dict(osc2_shape=1, osc2_level=127, osc2_semi=71, osc3_sync=1, osc3_shape=2, osc3_level=127),
                         ['osc2shape=1', 'osc2level=127', 'osc2semitone=7', 'osc3synctoosc2=1', 'osc3shape=2', 'osc3level=127']),
    'sync_o2saw': (dict(osc2_shape=1, osc2_level=127, osc2_semi=71, osc3_sync=1),
                   ['osc2shape=1', 'osc2level=127', 'osc2semitone=7', 'osc3synctoosc2=1']),
}

if __name__ == '__main__':
    for name, (cc, ov) in CASES.items():
        hw = os.path.join(ps.OUT, 'hw_%s.wav' % name)
        if not os.path.exists(hw):
            p2rig.set_sound(dict(ps.SILENT, **cc))
            time.sleep(0.3)
            cap = p2rig.capture(hw, ps.HOLD + 1.5, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(ps.NOTE, ps.HOLD))
            cap.communicate()
        p2 = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'pol_%s.wav' % name)
        subprocess.run(['./p2render', '-', str(ps.NOTE), str(ps.HOLD), '0.3', p2, '192000', *ps.BASE_ENGINE, *ov], check=True, capture_output=True)
        a, b = ps.cycle(hw, 1.0), ps.cycle(p2, 10.0)
        A, B = (a - a.mean()) / a.std(), (b - b.mean()) / b.std()
        res = {s: max(np.dot(A, np.roll(s * B, j)) / len(A) for j in range(256)) for s in (1, -1)}
        ch = ' .:-=+*#%@'
        print('%-18s same %.3f  inverted %.3f' % (name, res[1], res[-1]))
        for n, v in (('hw', A), ('p2', B)):
            print('   %s |%s|' % (n, ''.join(ch[min(9, int((x - v.min()) / np.ptp(v) * 9.99))] for x in v[::4])))
