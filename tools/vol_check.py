#!/usr/bin/python3
# The output-stage check (todo, Rig): at one position of the front-panel master knob, a 1 kHz sine into EXT at
# -30/-20/-10 dBFS, then osc 1 saw at note 48. Compare positions after level-matching.
# usage: vol_check.py <outdir> <label>     e.g. vol_check.py /Volumes/ext-ssd/Captures/Pulse2/192k/volcheck 3oclock
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

TONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'G2-Edit', 'tools', 'tone')
RATE = 192000
LEVELS = (-30, -20, -10)
HOLD_S = 2.0


def harmonics(seg, rate, f0, count=5):
    win = np.hanning(len(seg))
    t = np.arange(len(seg)) / rate
    h = [abs(np.sum(seg * win * np.exp(-2j * np.pi * f0 * k * t))) for k in range(1, count + 1)]
    return [20 * np.log10(np.sqrt(np.mean(seg ** 2)))] + [20 * np.log10(v / h[0] + 1e-12) for v in h[1:]]


def ext_series(outdir, label):
    p2rig.set_sound(dict(osc1_level=0, osc3_shape=3, osc3_level=127, osc3_routing=0, volume=40))
    path = os.path.join(outdir, 'ext1k_%s.wav' % label)
    cap = p2rig.capture(path, 1.5 + len(LEVELS) * HOLD_S + 1.0, RATE)
    time.sleep(0.8)
    p2rig.send(p2rig.hexmsg(0x90 | (p2rig.CHANNEL - 1), 60, 100))
    subprocess.run([TONE, '--device', 'Fireface', '--channels', str(p2rig.EXT_OUT_CHANNEL), '--hz', '1000',
                    '--db', ','.join(str(l) for l in LEVELS), '--hold', str(HOLD_S)], check=True, capture_output=True)
    p2rig.send(p2rig.hexmsg(0x80 | (p2rig.CHANNEL - 1), 60, 0))
    cap.communicate()
    x2, rate = read(path)
    x = x2[:, 0]
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    start = np.flatnonzero(env > 10 ** (-60 / 20))[0]
    rows = []
    for i, lv in enumerate(LEVELS):
        a = start + int((i * HOLD_S + 0.6) * rate)
        rows.append((lv, harmonics(x[a:a + int(0.8 * rate)], rate, 1000.0)))
    return rows


def saw(outdir, label):
    path = os.path.join(outdir, 'saw48_%s.wav' % label)
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'osc_capture.py'), path, '1',
                    'volume=40', 'notes=48'], check=True, capture_output=True)
    x2, rate = read(path)
    x = x2[:, 0]
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    start = np.flatnonzero(env > env.max() * 0.1)[0]
    return harmonics(x[start + int(0.3 * rate):start + int(1.0 * rate)], rate, 130.8135, 8)


if __name__ == '__main__':
    outdir, label = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for lv, h in ext_series(outdir, label):
        print('%-8s EXT 1 kHz at %+d dBFS in: out %6.1f dBFS  H2 %6.1f  H3 %6.1f  H4 %6.1f  H5 %6.1f' % (label, lv, *h))
    h = saw(outdir, label)
    print('%-8s saw note 48: %6.1f dBFS  H2..H8 %s' % (label, h[0], ' '.join('%6.1f' % v for v in h[1:])))
