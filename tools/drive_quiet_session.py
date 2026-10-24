#!/usr/bin/python3
# Does the drive lose level on a quiet SIGNAL, beyond the output gate? A saw at Level 127 (the gate fully open) through
# BP12, the cutoff stepped away from the note so the drive's input falls; TUBE and FUZZ at Drive 32 against NONE.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
import drive_gate_session as dg

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/drive_quiet'
CUTS = (40, 64, 80, 96, 110)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = os.environ.get('TMPDIR', '/tmp')
    print('BP12 cutoff | instrument NONE, TUBE-NONE, FUZZ-NONE | engine NONE, TUBE-NONE, FUZZ-NONE')
    for cut in CUTS:
        h, e = [], []
        for curve in (0, 1, 2):
            hw = os.path.join(OUT, 'hw_c%d_d%d.wav' % (cut, curve))
            if not os.path.exists(hw):
                p2rig.set_sound(dict(osc1_shape=1, osc1_level=127, cutoff=cut, vcf_type=2, volume=40, drive=32, drive_curve=curve))
                time.sleep(0.3)
                cap = p2rig.capture(hw, 2.5, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(48, 1.5))
                cap.communicate()
            h.append(dg.rms(hw, 1.0))
            p = os.path.join(d, 'dq_%d_%d.wav' % (cut, curve))
            subprocess.run(['./p2render', '-', '48', '1.5', '0.2', p, '192000', *sq.ENGINE_BASE, 'osc1shape=1', 'osc1level=127',
                            'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=%d' % cut, 'resonance=0', 'filtertype=2',
                            'volume=40', 'drive=32', 'drivecurve=%d' % curve], check=True, capture_output=True)
            e.append(dg.rms(p, 10.0))
        print('   %3d      | %6.1f %+6.1f %+6.1f | %6.1f %+6.1f %+6.1f' % (cut, h[0], h[1] - h[0], h[2] - h[0], e[0], e[1] - e[0], e[2] - e[0]))
