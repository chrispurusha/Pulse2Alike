#!/usr/bin/python3
# Osc 3's routings: osc 3 as a slow square (note 24, 24 semitones down: about 8 Hz) so its effect flips between two
# states. VCF: the self-oscillating filter's pitch, in cutoff steps. LEVEL2: osc 2's level, in dB.
# usage: osc3_session.py <outdir> vcf|level2
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from lfo_session import steps_track
from osc_analyse import read

RATE = 192000
LEVELS = (32, 64, 96, 127)
NOTE = 24
OSC3_HZ = 440.0 * 2 ** ((NOTE - 24 - 69) / 12.0)


def take(outdir, tag, sound, seconds=1.6):
    p2rig.set_sound(dict(osc1_level=0, osc3_shape=0, osc3_semi=64 - 24, volume=40, **sound))
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(NOTE, seconds))
    cap.communicate()
    return path


def two_states(t, v):
    # a square spends half its time in each state: the 20th and 80th percentiles are one inside each, whatever
    # osc 3's exact frequency (the DCO's lowest notes need not be on pitch)
    return np.percentile(v, 20), np.percentile(v, 80)


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    if what == 'vcf':
        print('osc 3 square -> VCF: the cutoff swing (steps) by osc 3 level')
        for lv in LEVELS:
            p = os.path.join(outdir, 'vcf_%d.wav' % lv)
            g, s = steps_track(p if os.environ.get('P2_REANALYSE') else take(outdir, 'vcf_%d' % lv, dict(osc3_routing=2, osc3_level=lv, resonance=127, cutoff=64)))
            sel = g > g[0] + 0.25
            lo, hi = two_states(g[sel], s[sel])
            print('  level %3d: %.1f to %.1f, swing %.1f steps' % (lv, lo, hi, hi - lo))
    elif what == 'level2':
        print('osc 3 square -> osc 2 level (osc 2 saw at level 64): the two levels (dBFS) by osc 3 level')
        for lv in LEVELS:
            p = os.path.join(outdir, 'level2_%d.wav' % lv)
            if not os.environ.get('P2_REANALYSE'):
                p = take(outdir, 'level2_%d' % lv, dict(osc3_routing=1, osc3_level=lv, osc2_level=64, osc2_shape=1, osc2_semi=64 + 24))
            x2, r = read(p)
            x = x2[:, 0]
            n = int(r / OSC3_HZ / 8)
            env = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode='same'))[::n // 4]
            t = np.arange(len(env)) * (n // 4) / r
            on = t[np.flatnonzero(env > env.max() * 0.05)[0]]
            sel = (t > on + 0.3) & (t < on + 1.4)
            lo, hi = two_states(t[sel], 20 * np.log10(env[sel] + 1e-9))
            print('  level %3d: %.1f and %.1f dBFS, %.1f dB apart' % (lv, lo, hi, hi - lo))


if __name__ == '__main__':
    main()
