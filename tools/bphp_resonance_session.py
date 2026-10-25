#!/usr/bin/python3
# BP12 and HP12's resonance from the noise alone (as resonance_response.py does LP24/LP12): cutoff 64, resonance
# 0/41/60/80/92, the instrument against the engine, each against its own resonance 0.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from resonance_response import psd, CENT

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/bphp_res'
RES = (0, 41, 60, 80, 92)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = os.environ.get('TMPDIR', '/tmp')
    print('dB against resonance 0 at %s Hz; engine - instrument' % ' '.join(str(c) for c in CENT))
    for mode, name in ((2, 'BP12'), (3, 'HP12')):
        spec = {}
        for res in RES:
            hw = os.path.join(OUT, 'hw_%s_r%d.wav' % (name, res))
            if not os.path.exists(hw):
                p2rig.set_sound(dict(osc1_level=0, noise=104, cutoff=64, resonance=res, vcf_type=mode, volume=40))
                time.sleep(0.3)
                cap = p2rig.capture(hw, 3.2, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(48, 2.2))
                cap.communicate()
            p2 = os.path.join(d, 'bh_%s_%d.wav' % (name, res))
            subprocess.run(['./p2render', '-', '48', '2.2', '0.2', p2, '192000', *sq.ENGINE_BASE, 'osc1level=0', 'osc2level=0',
                            'osc3level=0', 'noiselevel=104', 'cutoff=64', 'resonance=%d' % res, 'filtertype=%d' % mode, 'volume=40'],
                           check=True, capture_output=True)
            spec[res] = (psd(hw), psd(p2))
        f = spec[0][0][0]
        for res in RES[1:]:
            rows = []
            for k in (0, 1):
                d0 = spec[res][k][1] - spec[0][k][1]
                rows.append(np.array([np.mean(d0[(f > c * 0.97) & (f < c * 1.03)]) for c in CENT]))
            print('%s r%-3d hw %s\n           d  %s' % (name, res, ' '.join('%5.1f' % v for v in rows[0]), ' '.join('%+5.1f' % v for v in rows[1] - rows[0])))
