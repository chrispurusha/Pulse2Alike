#!/usr/bin/python3
# The drive's output gate against the cutoff (p2Plugin notes §55): a saw at Level 30 through LP12, no envelope, the
# cutoff stepped, FUZZ at Drive 17 against NONE - the drop beyond the curve's own is the gate. Instrument and engine.
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/drive_gate'
CUTS = (8, 12, 16, 20, 24, 32, 40, 64)


def rms(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    env = np.sqrt(np.convolve(x ** 2, np.ones(r // 100) / (r // 100), 'same'))
    on = np.flatnonzero(env > env.max() * 0.1)
    on = on[0] if len(on) else 0
    s = x[on + int(0.3 * r):on + int(1.3 * r)]
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12)


def settings(cut, curve):
    return dict(osc1_shape=1, osc1_level=30, cutoff=cut, vcf_type=1, volume=40, drive=17, drive_curve=curve)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for cut in CUTS:
        for curve in (0, 2):
            hw = os.path.join(OUT, 'hw_c%d_d%d.wav' % (cut, curve))
            if not os.path.exists(hw):
                p2rig.set_sound(settings(cut, curve))
                time.sleep(0.3)
                cap = p2rig.capture(hw, 2.5, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(48, 1.5))
                cap.communicate()
    d = os.environ.get('TMPDIR', '/tmp')
    print('cutoff | instrument NONE, FUZZ-NONE | engine NONE, FUZZ-NONE   (dBFS / dB)')
    for cut in CUTS:
        e = []
        for curve in (0, 2):
            p = os.path.join(d, 'gate_%d_%d.wav' % (cut, curve))
            subprocess.run(['./p2render', '-', '48', '1.5', '0.2', p, '192000', *sq.ENGINE_BASE, 'osc1shape=1', 'osc1level=30',
                            'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=%d' % cut, 'resonance=0', 'filtertype=1',
                            'volume=40', 'drive=17', 'drivecurve=%d' % curve], check=True, capture_output=True)
            e.append(rms(p, 10.0))
        h = [rms(os.path.join(OUT, 'hw_c%d_d%d.wav' % (cut, c)), 1.0) for c in (0, 2)]
        print('  %3d  | %6.1f  %+6.1f | %6.1f  %+6.1f' % (cut, h[0], h[1] - h[0], e[0], e[1] - e[0]))
