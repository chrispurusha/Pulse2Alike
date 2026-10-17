#!/usr/bin/python3
# LFO measurements (todo, Engine): an LFO into the cutoff of the self-oscillating filter (resonance 127, no
# input), whose pitch track is then the LFO's waveform in cutoff steps.
# usage: lfo_session.py <outdir> rate|shapes|amount|lfo2
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from mod_step import cycle_track
from fenv_session import cutoff_steps

RATE = 192000
SRC = {'lfo1': 1, 'lfo2': 4}
TGT_CUTOFF = 10


def take(outdir, tag, seconds, source='lfo1', speed=64, shape=1, amount=96, cutoff=64, extra=None):
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    p2rig.set_sound(dict(osc1_level=0, resonance=127, cutoff=cutoff, volume=40, **(extra or {})))
    speed_cc, shape_cc = (p2rig.CC_LFO1_SPEED, p2rig.CC_LFO1_SHAPE) if source == 'lfo1' else (26, None)
    items = [p2rig.hexmsg(ch, speed_cc, speed), p2rig.hexmsg(ch, 108, SRC[source]), p2rig.hexmsg(ch, 110, TGT_CUTOFF),
             p2rig.hexmsg(ch, 109, amount)]
    if shape_cc is not None:
        items.append(p2rig.hexmsg(ch, shape_cc, shape))
    p2rig.send(*items)
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(60, seconds))
    cap.communicate()
    return path


def steps_track(path, rate=2000.0):
    t, f = cycle_track(path)
    ok = (f > 20) & (f < 25000)
    t, s = t[ok], cutoff_steps(f[ok])
    g = np.arange(t[0] + 0.05, t[-1] - 0.05, 1.0 / rate)
    return g, np.interp(g, t, s)


def period(g, s):
    x = s - s.mean()
    n = 1 << int(np.ceil(np.log2(4 * len(x))))
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), n))
    f = np.fft.rfftfreq(n, g[1] - g[0])
    k = int(np.argmax(X[2:])) + 2
    return f[k]


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    if what == 'rate':
        print('LFO 1 triangle: speed -> Hz (cutoff swing p-p in steps)')
        for sp in list(range(0, 128, 8)) + [127]:
            secs = 8.0 if sp < 24 else (4.0 if sp < 64 else 2.5)
            g, s = steps_track(take(outdir, 'rate_%d' % sp, secs, speed=sp, shape=1))
            print('  %3d %8.3f Hz  p-p %.1f' % (sp, period(g, s), np.percentile(s, 99) - np.percentile(s, 1)))
    elif what == 'shapes':
        names = ['SINE', 'TRI', 'SAW', 'SQR', 'S&H', 'sSIN', 'sTRI', 'sSAW', 'sSQR', 'sS&H']
        print('LFO 1 shapes at speed 40: one period of the cutoff track (16 points, steps from the mean)')
        for sh in range(10):
            g, s = steps_track(take(outdir, 'shape_%d' % sh, 4.0, speed=40, shape=sh))
            hz = period(g, s)
            ph = ((g - g[0]) * hz) % 1.0
            b = np.minimum((ph * 16).astype(int), 15)
            prof = np.bincount(b, s, 16) / np.maximum(np.bincount(b, None, 16), 1)
            print('  %-5s %.3f Hz: %s' % (names[sh], hz, ' '.join('%+.1f' % v for v in (prof - prof.mean()))))
    elif what == 'amount':
        print('LFO 1 triangle, speed 40: mod amount -> cutoff swing p-p (steps)')
        for a in (64, 68, 72, 80, 88, 96, 112, 127, 56, 32, 0):
            g, s = steps_track(take(outdir, 'amount_%d' % a, 3.0, speed=40, shape=1, amount=a))
            print('  %3d %.2f' % (a, np.percentile(s, 99) - np.percentile(s, 1)))
    elif what == 'lfo2':
        print('LFO 2 (its own shape): speed -> Hz, and delay')
        for sp in (16, 40, 64, 96):
            g, s = steps_track(take(outdir, 'lfo2_rate_%d' % sp, 4.0, source='lfo2', speed=sp))
            print('  speed %3d %8.3f Hz' % (sp, period(g, s)))
        for dl in (0, 32, 64, 96):
            g, s = steps_track(take(outdir, 'lfo2_delay_%d' % dl, 6.0, source='lfo2', speed=64, extra=dict()))
            print('  delay %3d: swing in successive 0.5 s windows: %s' % (dl, ' '.join(
                '%.1f' % (np.ptp(s[(g >= g[0] + i * 0.5) & (g < g[0] + (i + 1) * 0.5)]) if ((g >= g[0] + i * 0.5) & (g < g[0] + (i + 1) * 0.5)).any() else 0.0)
                for i in range(10))))


if __name__ == '__main__':
    main()
