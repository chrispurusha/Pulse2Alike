#!/usr/bin/python3
# Glide: the time law against Glide Rate, and what each Glide Mode does with separate and legato notes.
# The saw's pitch is tracked cycle by cycle. usage: glide_session.py <outdir> rate|mode
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from mod_step import cycle_track

RATE = 192000
MODES = ['OFF', 'NORM', 'FNGR', 'FNON', 'FOFF']


def take(outdir, tag, sound, items, seconds):
    p2rig.set_sound(dict(volume=40, osc1_shape=2, cutoff=127, **sound))   # TRI: one clean crossing per cycle
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*items)
    cap.communicate()
    return path


def track_semis(path):
    import wave
    from scipy.signal import butter, sosfiltfilt
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    x = sosfiltfilt(butter(4, 380.0, 'low', fs=r, output='sos'), x)      # below note 48's 3rd harmonic
    i = np.flatnonzero((x[:-1] < 0) & (x[1:] >= 0))
    tc = (i + (-x[i] / (x[i + 1] - x[i]))) / r
    t, f = tc[1:], 1.0 / np.diff(tc)
    ok = (f > 50) & (f < 2000)
    t, f = t[ok], f[ok]
    s = 12 * np.log2(f / 440.0) + 69
    # one-cycle glitches out: a median over 5 cycles
    sm = np.array([np.median(s[max(0, i - 2):i + 3]) for i in range(len(s))])
    return t, sm


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    ch = p2rig.CHANNEL - 1
    on = lambda n: p2rig.hexmsg(0x90 | ch, n, 100)
    off = lambda n: p2rig.hexmsg(0x80 | ch, n, 0)
    if what == 'rate':
        print('NORM glide 48 -> 60 (legato): seconds to cover 10/50/90 % of the octave')
        for rate in (16, 32, 48, 64, 80, 96, 112, 127):
            p = take(outdir, 'rate_%d' % rate, dict(glide_mode=1, glide_rate=rate),
                     [on(48), 'sleep:600', on(60), 'sleep:6000', off(60), off(48)], 6.6)
            t, s = track_semis(p)
            t0 = t[np.flatnonzero(s > 48.5)[0]] if (s > 48.5).any() else np.nan
            marks = []
            for frac in (0.1, 0.5, 0.9):
                i = np.flatnonzero(s >= 48 + 12 * frac)
                marks.append('%.3f' % (t[i[0]] - t0) if len(i) else '-')
            print('  rate %3d: %s   (final %.2f)' % (rate, ' / '.join(marks), np.median(s[-50:])))
    elif what == 'mode':
        print('each mode, rate 80: separate notes 48 then 60, then legato 48 -> 60 (pitch at 20/100/400 ms after the 2nd note)')
        for m in range(5):
            row = []
            for legato in (False, True):
                items = ([on(48), 'sleep:600', off(48), 'sleep:300', on(60), 'sleep:1500', off(60)] if not legato
                         else [on(48), 'sleep:600', on(60), 'sleep:1500', off(60), off(48)])
                p = take(outdir, 'mode_%s_%s' % (MODES[m], 'leg' if legato else 'sep'), dict(glide_mode=m, glide_rate=80), items, 2.6)
                t, s = track_semis(p)
                start = t[0]
                second = start + (0.9 if not legato else 0.6)
                row.append(' '.join('%.1f' % np.interp(second + dt, t, s) for dt in (0.02, 0.1, 0.4)))
            print('  %-4s separate: %-16s legato: %s' % (MODES[m], row[0], row[1]))


if __name__ == '__main__':
    main()
