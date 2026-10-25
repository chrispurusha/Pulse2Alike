#!/usr/bin/python3
# A library sound taken apart: the sound's .syx into the edit buffer, then CC overrides per variant, on the
# instrument and the engine alike; octave bands over the sustain, engine minus instrument.
# usage: patch_variant.py <nnn> <note> <variant>=<cc:value,...>[;<renderer overrides>] ...
#        e.g. patch_variant.py 10 48 asis= open=50:127,52:64;cutoff=127,filterenvamount=64
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/variants'
PATCHES = '/Volumes/ext-ssd/Captures/Pulse2/192k/patches'
OCTAVES = (125, 250, 500, 1000, 2000, 4000, 8000)
HOLD = 2.5


def bands(path, gain):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    env = np.sqrt(np.convolve(x ** 2, np.ones(r // 200) / (r // 200), 'same'))
    on = np.flatnonzero(env > env.max() * 0.05)[0]
    s = x[on + int(0.5 * r):on + int((HOLD - 0.2) * r)]
    S = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / r)
    return np.array([10 * np.log10(S[(f >= c / np.sqrt(2)) & (f < c * np.sqrt(2))].sum() + 1e-20) for c in OCTAVES]), \
        10 * np.log10(np.mean(s ** 2))


def main():
    n, note = int(sys.argv[1]), int(sys.argv[2])
    syx = os.path.join(PATCHES, 'fixedlfo_%03d.syx' % n)
    os.makedirs(OUT, exist_ok=True)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    print('engine - instrument, octaves %s' % ' '.join('%5d' % c for c in OCTAVES))
    for arg in sys.argv[3:]:
        tag, spec = arg.split('=', 1)
        ccs, _, ren = spec.partition(';')
        pairs = [tuple(int(v) for v in kv.split(':')) for kv in ccs.split(',') if kv]
        hw = os.path.join(OUT, 'hw_%03d_n%d_%s.wav' % (n, note, tag))
        if not os.path.exists(hw):
            p2rig.send(open(syx, 'rb').read().hex(), 'sleep:400', p2rig.hexmsg(ch, 1, 0), *[p2rig.hexmsg(ch, c, v) for c, v in pairs])
            time.sleep(0.4)
            cap = p2rig.capture(hw, HOLD + 1.5, 192000)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(note, HOLD))
            cap.communicate()
        p2 = os.path.join(os.environ['TMPDIR'], 'variant.wav')
        subprocess.run([render, syx, str(note), str(HOLD), '0.3', p2, '192000', *[o for o in ren.split(',') if o]],
                       check=True, capture_output=True)
        bh, lh = bands(hw, 1.0)
        bp, lp = bands(p2, 10.0)
        print('%-10s level %+5.1f dB | %s' % (tag, lp - lh, ' '.join('%+5.1f' % (b - a) for a, b in zip(bh, bp))))


if __name__ == '__main__':
    main()
