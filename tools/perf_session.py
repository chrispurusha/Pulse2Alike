#!/usr/bin/python3
# The performance controls on the instrument: bend range, the mod wheel and pressure as mod sources (on the
# self-oscillating filter's cutoff, in steps), and the sustain pedal. usage: perf_session.py <outdir>
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from lfo_session import steps_track, TGT_CUTOFF
from osc_analyse import read, refine_f0

RATE = 192000
CH = p2rig.CHANNEL - 1


def capture(outdir, tag, sound, items, seconds):
    p2rig.set_sound(dict(volume=40, **sound))
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*items)
    cap.communicate()
    return path


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    on, off = p2rig.hexmsg(0x90 | CH, 48, 100), p2rig.hexmsg(0x80 | CH, 48, 0)
    # bend: up full, then down full, 0.5 s each, Bend Up 2 / Down 12
    bend = lambda v: p2rig.hexmsg(0xE0 | CH, v & 0x7F, v >> 7)
    p = capture(outdir, 'bend', dict(), [p2rig.hexmsg(0xB0 | CH, 105, 2), p2rig.hexmsg(0xB0 | CH, 106, 12), bend(8192), on,
                                        'sleep:500', bend(16383), 'sleep:500', bend(0), 'sleep:500', bend(8192), off], 1.6)
    x2, r = read(p)
    x = x2[:, 0]
    st = np.flatnonzero(np.abs(x) > 1e-3)[0]
    for name, t0, guess in (('rest', 0.15, 130.8), ('up', 0.65, 146.8), ('down', 1.15, 65.4)):
        s = x[st + int(t0 * r):st + int((t0 + 0.3) * r)]
        f = refine_f0(s - s.mean(), r, guess)
        print('bend %-4s %.2f Hz (%+.2f semitones)' % (name, f, 12 * np.log2(f / 130.8128)))
    # wheel and pressure on the cutoff: amount 96 (+32 steps at full)
    for name, src, msg in (('wheel', 12, lambda v: p2rig.hexmsg(0xB0 | CH, 1, v)), ('pressure', 13, lambda v: p2rig.hexmsg(0xD0 | CH, v))):
        items = [p2rig.hexmsg(0xB0 | CH, 108, src), p2rig.hexmsg(0xB0 | CH, 110, TGT_CUTOFF), p2rig.hexmsg(0xB0 | CH, 109, 96),
                 msg(0), on, 'sleep:600', msg(64), 'sleep:600', msg(127), 'sleep:600', off, msg(0)]
        g, s = steps_track(capture(outdir, name, dict(osc1_level=0, resonance=127, cutoff=48), items, 1.8))
        lv = [np.median(s[(g > g[0] + a) & (g < g[0] + a + 0.3)]) for a in (0.25, 0.85, 1.45)]
        print('%-8s 0 / 64 / 127: %.1f / %.1f / %.1f steps (rise %.1f, %.1f)' % (name, lv[0], lv[1], lv[2], lv[1] - lv[0], lv[2] - lv[0]))
    # sustain: note off at 0.4 s with the pedal down, pedal up at 1.2 s
    p = capture(outdir, 'sustain', dict(), [p2rig.hexmsg(0xB0 | CH, 64, 127), on, 'sleep:400', off, 'sleep:800',
                                           p2rig.hexmsg(0xB0 | CH, 64, 0)], 1.4)
    x2, r = read(p)
    x = x2[:, 0]
    n = r // 100
    e = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode='same'))[::n] + 1e-9)
    st = np.flatnonzero(e > e.max() - 30)[0]
    print('sustain level every 0.1 s:', ' '.join('%.0f' % v for v in e[st:st + 180:10]))


if __name__ == '__main__':
    main()
