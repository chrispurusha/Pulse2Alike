#!/usr/bin/python3
# The oscillator laws from osc_session.sh's law_* takes: level (rms against the level CC), detune and semitone
# (pitch against the CC, relative to the CC-64 take). usage: osc_laws.py <osc capture dir>
import glob, math, os, re, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osc_analyse import P2_CLOCK, period_ticks, read, refine_f0


def steady(path):
    x2, rate = read(path)
    x = x2[:, 0]
    env = np.sqrt(np.convolve(x ** 2, np.ones(rate // 100) / (rate // 100), mode='same'))
    on = np.flatnonzero(env > max(env.max() * 0.1, 1e-4))
    if len(on) == 0:
        return None, rate
    seg = x[on[0] + int(0.3 * rate):on[0] + int(1.0 * rate)]
    return seg - seg.mean(), rate


def law(d, name, note, guess_semitones):
    rows = []
    for p in glob.glob(os.path.join(d, 'law_%s_*.wav' % name)):
        v = int(re.search(r'_(\d+)\.wav$', p).group(1))
        seg, rate = steady(p)
        if seg is None:
            rows.append((v, None, None)); continue
        rms = 20 * math.log10(np.sqrt(np.mean(seg ** 2)))
        f = None
        if guess_semitones is not None:
            guess = P2_CLOCK / period_ticks(note) * 2 ** (guess_semitones(v) / 12)
            # coarse first: the fundamental's peak within 1.5 semitones of the guess, then refined
            n = 1 << 21
            X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
            fr = np.fft.rfftfreq(n, 1 / rate)
            band = (fr > guess * 2 ** (-1.5 / 12)) & (fr < guess * 2 ** (1.5 / 12))
            f = refine_f0(seg, rate, fr[band][np.argmax(X[band])])
        rows.append((v, rms, f))
    return sorted(rows)


def main():
    d = sys.argv[1]
    print('LEVEL (osc 1 saw, note 48): CC -> rms dBFS, and relative to CC 127')
    rows = law(d, 'level', 48, None)
    top = [r for v, r, _ in rows if v == 127][0]
    print('  ' + ' '.join('%d:%s' % (v, ('%.1f(%+.1f)' % (r, r - top)) if r is not None else 'silent') for v, r, _ in rows))
    for name, guess in (('detune', lambda v: 0.0), ('semi', lambda v: v - 64)):
        rows = law(d, name, 60, guess)
        ref = [f for v, _, f in rows if v == 64][0]
        print('%s (note 60): CC -> cents from CC 64' % name.upper())
        print('  ' + ' '.join('%d:%+.1f' % (v, 1200 * math.log2(f / ref)) for v, _, f in rows if f))


main()
