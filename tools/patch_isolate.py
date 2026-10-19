#!/usr/bin/python3
# A library sound taken apart: sent to the edit buffer (LFO phases fixed at 0), CC overrides on top, on the instrument
# and the engine alike; level and brightness (1.5-12 kHz over the fundamental) over time.
# usage: patch_isolate.py <patch> <note> <tag:cc=v,cc=v:title=v,title=v> ...
import glob, os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

LIB = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/Patches/Pulse2')
OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/isolate'
HERE = os.path.dirname(os.path.abspath(__file__))


def track(p, f0, g=1.0):
    x2, r = read(p)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * g
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.02)[0]
    lv, br = [], []
    for t0 in np.arange(0.0, 1.6, 0.2):
        s = x[on + int(t0 * r):on + int((t0 + 0.2) * r)]
        X = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
        f = np.fft.rfftfreq(len(s), 1 / r)
        lv.append(20 * np.log10(np.sqrt(np.mean((s - s.mean()) ** 2)) + 1e-12))
        br.append(10 * np.log10(X[(f > 1500) & (f < 12000)].sum() / X[(f > f0 * 0.8) & (f < f0 * 1.25)].sum() + 1e-12))
    return np.array(lv), np.array(br)


def main():
    n, note = int(sys.argv[1]), int(sys.argv[2])
    os.makedirs(OUT, exist_ok=True)
    syx = bytearray(open(glob.glob(os.path.join(LIB, '%03d *.syx' % n))[0], 'rb').read())
    syx[5], syx[6] = 0x7F, 0
    syx[7 + 81] = syx[7 + 82] = 2
    syx[135] = sum(syx[1:135]) & 0x7F
    fx = os.path.join(OUT, 'p%03d_fixed.syx' % n)
    open(fx, 'wb').write(syx)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    f0 = 440.0 * 2 ** ((note - 69) / 12.0)
    for arg in sys.argv[3:]:
        tag, ccs, titles = (arg.split(':') + ['', ''])[:3]
        cc = [tuple(int(v) for v in kv.split('=')) for kv in ccs.split(',') if kv]
        ov = [kv for kv in titles.split(',') if kv]
        hw = os.path.join(OUT, 'hw_%03d_n%d_%s.wav' % (n, note, tag))
        p2rig.send(bytes(syx).hex(), 'sleep:300', *[p2rig.hexmsg(ch, c, v) for c, v in cc])
        time.sleep(0.3)
        cap = p2rig.capture(hw, 2.6, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(note, 1.6))
        cap.communicate()
        en = os.path.join(OUT, 'p2_%03d_n%d_%s.wav' % (n, note, tag))
        subprocess.run([os.path.join(HERE, 'p2render'), fx, str(note), '1.6', '0.5', en, '192000', *ov], check=True, capture_output=True)
        (lh, bh), (le, be) = track(hw, f0), track(en, f0, 10.0)
        print('%-8s level eng-hw %s | bright eng-hw %s' % (tag, ' '.join('%+5.1f' % v for v in le - lh), ' '.join('%+5.1f' % v for v in be - bh)))


if __name__ == '__main__':
    main()
