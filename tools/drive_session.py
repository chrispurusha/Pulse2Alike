#!/usr/bin/python3
# Drive and its curves: a 1 kHz sine into EXT at three levels, per drive amount and curve; gain and harmonics.
# usage: drive_session.py <outdir>
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read
from vol_check import harmonics, TONE, RATE, LEVELS, HOLD_S

CURVES = ['NONE', 'TUBE', 'FUZZ', 'FX']


def series(outdir, tag, sound, hz=1000.0):
    p2rig.set_sound(dict(osc1_level=0, osc3_shape=3, osc3_level=127, osc3_routing=0, volume=40, **sound))
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, 1.5 + len(LEVELS) * HOLD_S + 1.0, RATE)
    time.sleep(0.8)
    p2rig.send(p2rig.hexmsg(0x90 | (p2rig.CHANNEL - 1), 60, 100))
    subprocess.run([TONE, '--device', 'Fireface', '--channels', str(p2rig.EXT_OUT_CHANNEL), '--hz', '%g' % hz,
                    '--db', ','.join(str(l) for l in LEVELS), '--hold', str(HOLD_S)], check=True, capture_output=True)
    p2rig.send(p2rig.hexmsg(0x80 | (p2rig.CHANNEL - 1), 60, 0))
    cap.communicate()
    x2, rate = read(path)
    x = x2[:, 0]
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    start = np.flatnonzero(env > 10 ** (-60 / 20))[0]
    return [harmonics(x[start + int((i * HOLD_S + 0.6) * rate):start + int((i * HOLD_S + 1.4) * rate)], rate, hz)
            for i in range(len(LEVELS))]


FREQS = (100.0, 300.0, 1000.0, 3000.0)


def main():
    outdir = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == 'freqs':
        # the curves' memory: the same sweep at four frequencies (NONE as each one's reference)
        for hz in FREQS:
            series(outdir, 'drive_NONE_0_f%d' % hz, dict(drive=0, drive_curve=0), hz)
            for c in (1, 2):
                for dr in (0, 32, 64, 127):
                    series(outdir, 'drive_%s_%d_f%d' % (CURVES[c], dr, hz), dict(drive=dr, drive_curve=c), hz)
            print('%g Hz done' % hz)
        return
    os.makedirs(outdir, exist_ok=True)
    print('curve drive | per input level (-30/-20/-10 dBFS): out dBFS  H2  H3  H5')
    for c in range(4):
        for dr in (0, 32, 64, 96, 127):
            rows = series(outdir, 'drive_%s_%d' % (CURVES[c], dr), dict(drive=dr, drive_curve=c))
            print('%-4s %3d | %s' % (CURVES[c], dr, ' | '.join('%6.1f %5.1f %5.1f %5.1f' % (h[0], h[1], h[2], h[4]) for h in rows)))


if __name__ == '__main__':
    main()
