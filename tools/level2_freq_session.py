#!/usr/bin/python3
# LEVEL2 against osc 3's frequency: osc 2 a saw at 2093 Hz (Level 101), osc 3 on LEVEL2 at Level 58 as SAW and SQR,
# at 16, 33, 65 and 131 Hz (osc 3 -48/-36/-24/-12 at note 60); osc 2's envelope folded on osc 3's period, instrument
# and engine: the swing (max - min, nepers) and the mean level.  usage: level2_freq_session.py
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import level2_session as ls

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/level2_freq'
SEMIS = (-48, -36, -24, -12)


def fold(path, gain, f3):
    ls.F3 = f3
    return ls.fold(path, gain, 64)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = os.environ.get('TMPDIR', '/tmp')
    print('osc 3 Hz  shape | instrument swing, mean | engine swing, mean')
    for shape, s3 in (('saw', 1), ('sqr', 0)):
        for semi in SEMIS:
            f3 = 261.6256 * 2 ** (semi / 12)
            res = []
            for lv in (0, 58):
                hw = os.path.join(OUT, 'hw_%s_s%d_l%d.wav' % (shape, semi, lv))
                if not os.path.exists(hw):
                    p2rig.set_sound(dict(osc1_level=0, osc2_shape=1, osc2_level=101, osc2_semi=64 + 36, osc3_shape=s3, osc3_routing=1,
                                         osc3_semi=64 + semi, osc3_level=lv, osc3_sync=0, cutoff=127, volume=40))
                    time.sleep(0.3)
                    cap = p2rig.capture(hw, 2.6, 192000)
                    time.sleep(0.8)
                    p2rig.send(*p2rig.note_items(60, 1.6))
                    cap.communicate()
                p2 = os.path.join(d, 'l2f_%s_%d_%d.wav' % (shape, semi, lv))
                ls.subprocess.run(['./p2render', '-', '60', '1.6', '0.2', p2, '192000', *ls.sq.ENGINE_BASE, 'osc1level=0', 'osc2shape=1',
                                   'osc2level=101', 'osc2semitone=36', 'osc3shape=%d' % s3, 'osc3routing=1', 'osc3semitone=%d' % semi,
                                   'osc3level=%d' % lv, 'osc3synctoosc2=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40'],
                                  check=True, capture_output=True)
                res.append((fold(hw, 1.0, f3), fold(p2, 10.0, f3)))
            (h0, e0), (h, e) = res
            hl, el = np.log(h / np.mean(h0)), np.log(e / np.mean(e0))
            print('  %6.1f  %s | %5.2f %+5.1f dB | %5.2f %+5.1f dB' % (f3, shape, np.ptp(np.maximum(hl, -5)), 8.686 * np.log(np.mean(np.exp(hl))),
                                                                  np.ptp(np.maximum(el, -5)), 8.686 * np.log(np.mean(np.exp(el)))))
