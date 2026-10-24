#!/usr/bin/python3
# Where in the cycle a pulse sits against the sync edge: osc 2 a narrow pulse (PW 40) synced at osc 3's pitch, osc 3's
# saw audible beside it (its reset marks the edge). One cycle folded; instrument against engine builds by circular
# correlation (the pulse's place against the saw's jump is what differs).  usage: pulse_phase_session.py <p2render>...
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
import polarity_session as ps

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/pulse_phase'

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    hw = os.path.join(OUT, 'hw_sync_pw40.wav')
    if not os.path.exists(hw):
        p2rig.set_sound(dict(osc1_level=0, osc2_shape=0, osc2_pw=40, osc2_level=127, osc3_shape=1, osc3_level=127,
                             osc3_sync=1, noise=0, cutoff=127, volume=40))
        time.sleep(0.3)
        cap = p2rig.capture(hw, 3.0, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(48, 2.0))
        cap.communicate()
    a = ps.cycle(hw, 1.0)
    A = (a - a.mean()) / a.std()
    ch = ' .:-=+*#%@'
    j = np.argmax(np.diff(A, append=A[0]))          # the saw's jump
    A = np.roll(A, -j - 1)
    print('instrument |%s|' % ''.join(ch[min(9, int((x - A.min()) / np.ptp(A) * 9.99))] for x in A[::4]))
    for b in sys.argv[1:]:
        p = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'pp.wav')
        subprocess.run([b, '-', '48', '2.0', '0.2', p, '192000', *ps.BASE_ENGINE, 'osc2shape=0', 'osc2pulsewidth=40', 'osc2level=127',
                        'osc3shape=1', 'osc3level=127', 'osc3synctoosc2=1'], check=True, capture_output=True)
        e = ps.cycle(p, 10.0)
        E = (e - e.mean()) / e.std()
        best = max(range(256), key=lambda k: np.dot(A, np.roll(E, k)))
        E = np.roll(E, best)
        print('%-10s |%s|  corr %.3f' % (os.path.basename(b)[:10], ''.join(ch[min(9, int((x - E.min()) / np.ptp(E) * 9.99))] for x in E[::4]),
                                       np.dot(A, E) / len(A)))
