#!/usr/bin/python3
# Brightness, instrument against engine: a library sound at a note and velocity; the energy above 1.5 kHz relative
# to the fundamental's third octave, in the attack and the sustain. usage: brightness.py <first,patches> <note> <velocities>
import glob, os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

LIB = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/Patches/Pulse2')
OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/brightness'
HERE = os.path.dirname(os.path.abspath(__file__))


def bright(path, f0, gain=1.0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.02)[0]
    out = []
    for a, b in ((0.02, 0.25), (0.6, 1.4)):
        s = x[on + int(a * r):on + int(b * r)]
        X = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
        f = np.fft.rfftfreq(len(s), 1 / r)
        fund = X[(f > f0 * 0.89) & (f < f0 * 1.12)].sum()
        high = X[(f > 1500) & (f < 12000)].sum()
        out.append(10 * np.log10(high / fund + 1e-12))
    s = x[on + int(0.6 * r):on + int(1.4 * r)]
    out.append(20 * np.log10(np.sqrt(np.mean((s - s.mean()) ** 2)) + 1e-12))
    return out


def main():
    patches = [int(v) for v in sys.argv[1].split(',')]
    notes = [int(v) for v in sys.argv[2].split(',')]
    vels = [int(v) for v in sys.argv[3].split(',')]
    os.makedirs(OUT, exist_ok=True)
    ch = p2rig.CHANNEL - 1
    print('engine minus instrument, dB: brightness (1.5-12 kHz over the fundamental) attack / sustain, and level')
    for n, note in [(n, note) for n in patches for note in notes]:
        f0 = 440.0 * 2 ** ((note - 69) / 12.0)
        syx = glob.glob(os.path.join(LIB, '%03d *.syx' % n))[0]
        for v in vels:
            hw = os.path.join(OUT, 'hw_%03d_n%d_v%d.wav' % (n, note, v))
            if not os.path.exists(hw):
                p2rig.send(p2rig.hexmsg(0xB0 | ch, 32, (n - 1) // 100), p2rig.hexmsg(0xC0 | ch, (n - 1) % 100), 'sleep:400')
                cap = p2rig.capture(hw, 3.8, 192000)
                time.sleep(0.8)
                p2rig.send(*p2rig.note_items(note, 1.6, velocity=v))
                cap.communicate()
            en = os.path.join(OUT, 'p2_%03d_n%d_v%d.wav' % (n, note, v))
            subprocess.run([os.path.join(HERE, 'p2render'), syx, str(note), '1.6', '1.0', en, '192000', 'vel=%d' % v],
                           check=True, capture_output=True)
            h, e = bright(hw, f0), bright(en, f0, 10.0)
            print('  P%03d note %d vel %3d: bright %+5.1f / %+5.1f   level %+5.1f' % (n, note, v, e[0] - h[0], e[1] - h[1], e[2] - h[2]))


if __name__ == '__main__':
    main()
