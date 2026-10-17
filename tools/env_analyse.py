#!/usr/bin/python3
# Reads env_session.sh's takes: per stage and value, the times to reach set levels, and the curve's shape.
# usage: env_analyse.py <env capture dir>
import glob, json, os, re, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_capture import envelope


def load(d, stage):
    out = []
    for p in glob.glob(os.path.join(d, '%s_*.wav' % stage)):
        v = int(re.search(r'_(\d+)\.wav$', p).group(1))
        meta = json.load(open(p[:-4] + '.json'))
        e, fs = envelope(p)
        out.append((v, e, fs, meta))
    return sorted(out, key=lambda t: t[0])


def crossing(db, start, level, rising):
    idx = np.flatnonzero((db[start:] >= level) if rising else (db[start:] <= level))
    return (start + idx[0]) if len(idx) else None


def main():
    d = sys.argv[1]
    full = None
    for v, e, fs, meta in load(d, 'sustain'):
        if v == 127:
            full = np.median(e[int(0.3 * fs):int(1.0 * fs)])
    print('full level (sustain 127): %.1f dBFS' % (20 * np.log10(full)))
    print('SUSTAIN: value -> dB re 127')
    print('  ' + ' '.join('%d:%.1f' % (v, 20 * np.log10(np.median(e[int(0.3 * fs):int(1.0 * fs)]) / full + 1e-9))
                          for v, e, fs, meta in load(d, 'sustain')))
    levels = (-40, -20, -12, -6, -3, -1)
    for stage in ('attack', 'decay', 'release'):
        order = levels if stage == 'attack' else tuple(reversed(levels))
        print('%s: value -> seconds to reach %s dB (from the stage start)' % (stage.upper(), '/'.join(str(l) for l in order)))
        for v, e, fs, meta in load(d, stage):
            db = 20 * np.log10(e / full + 1e-9)
            on = np.flatnonzero(db > -55)
            if len(on) == 0:
                print('  %3d silent' % v); continue
            if stage == 'attack':
                start, rising, lv = on[0], True, levels
            elif stage == 'decay':
                start, rising, lv = on[0] + int(np.argmax(db[on[0]:on[0] + int(0.05 * fs)])), False, tuple(reversed(levels))   # from the peak
            else:
                start = on[0] + int(meta['hold_s'] * fs)    # note off
                rising, lv = False, tuple(reversed(levels))
            ts = []
            for l in lv:
                c = crossing(db, start, l, rising)
                ts.append('%7.3f' % ((c - start) / fs) if c is not None else '      -')
            print('  %3d %s' % (v, ' '.join(ts)))


if __name__ == '__main__':
    main()
