#!/usr/bin/python3
# The arpeggiator, measured: tempo (inter-onset interval at Clock 1/16), the Clock values, Step Duration (the gate
# against the step), Swing, the modes' note order, and the step events. Each arp note is a pluck (amp envelope
# A 0, D 30, S 0) or, for gate lengths, held (S 127).
# usage: arp_session.py <outdir> tempo|clock|duration|swing|modes|events
import os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read, refine_f0

RATE = 96000
CH = p2rig.CHANNEL - 1
PLUCK = dict(enva_a=0, enva_d=30, enva_s=0, enva_r=0, enva_trigger=2, envf_trigger=2)   # RET1: every arp note plucks
CLOCK_1_16 = 12            # the list starts at 1/1: 12 is 1/16 (13 is 3/64)


def take(outdir, tag, sound, notes, seconds, step_bytes=None):
    p2rig.set_sound(dict(dict(volume=40, arp_active=1, arp_range=0, arp_mode=0, arp_clock=CLOCK_1_16, arp_tempo=64,
                              arp_step=8, arp_swing=64, arp_delay=64, arp_length=15), **sound))
    if step_bytes is not None:
        p2rig.set_step_bytes(step_bytes)
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    on = [p2rig.hexmsg(0x90 | CH, n, 100) for n in notes]
    off = [p2rig.hexmsg(0x80 | CH, n, 0) for n in notes]
    p2rig.send(*on, 'sleep:%d' % int(seconds * 1000), *off)
    cap.communicate()
    return path


def onsets(path):
    # 2 ms RMS every 0.25 ms; an onset is a rise through -10 dB after the level has been below -25
    x2, r = read(path)
    x = x2[:, 0]
    w, hop = r // 500, r // 4000
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, mode='same'))[::hop]
    db = 20 * np.log10(e / e.max() + 1e-9)
    out, armed = [], True
    for i in range(1, len(db)):
        if armed and db[i] > -10:
            out.append(i * hop / r)
            armed = False
        elif db[i] < -25:
            armed = True
    return np.array(out), x, r, db


def gates(path):
    # with the envelope held, a gate is the level between a rise through -10 dB and the next fall through -30 dB
    t, x, r, db = onsets(path)
    hop = r // 4000
    lens = []
    for a in t:
        i = int(a * r / hop)
        j = i + np.argmax(db[i:] < -30) if np.any(db[i:] < -30) else len(db)
        lens.append((j - i) * hop / r)
    return t, np.array(lens)


def pitches(path, t, x, r):
    # autocorrelation over 40 ms from 8 ms after each onset, between 50 and 1000 Hz, as a MIDI note
    out = []
    for a in t:
        s = x[int((a + 0.008) * r):int((a + 0.048) * r)]
        s = s - s.mean()
        if len(s) < r // 50:
            out.append(-1)
            continue
        ac = np.correlate(s, s, 'full')[len(s) - 1:]
        lo, hi = r // 1000, r // 50
        k = lo + int(np.argmax(ac[lo:hi]))
        out.append(int(round(69 + 12 * np.log2((r / k) / 440.0))))
    return out


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    if what == 'tempo':
        print('Tempo value -> BPM (Clock 1/16: four steps to a beat)')
        for tv in (0, 8, 16, 32, 48, 64, 80, 96, 112, 127):
            t, *_ = onsets(take(outdir, 'tempo_%d' % tv, dict(arp_tempo=tv, **PLUCK), [48], 3.0 if tv > 16 else 5.0))
            iv = np.median(np.diff(t))
            print('  %3d: step %.4f s -> %.2f BPM' % (tv, iv, 60.0 / (4 * iv)))
    elif what == 'clock':
        print('Clock value -> step at tempo 64, in sixteenths of the tempo-64 step')
        ref = None
        for cv in range(0, 20):
            secs = 6.0 if cv < 4 else 3.0
            t, *_ = onsets(take(outdir, 'clock_%d' % cv, dict(arp_clock=cv, **PLUCK), [48], secs))
            iv = np.median(np.diff(t)) if len(t) > 2 else float('nan')
            print('  %2d: step %.4f s' % (cv, iv))
    elif what == 'duration':
        print('Step Duration value -> gate / step (held envelope)')
        for dv in range(0, 15):
            p = os.path.join(outdir, 'dur_%d.wav' % dv)
            if not os.environ.get('P2_REANALYSE'):
                p = take(outdir, 'dur_%d' % dv, dict(arp_step=dv, enva_a=0, enva_d=0, enva_s=127, enva_r=0, enva_trigger=2), [48], 2.5)
            up, lens = gates(p)
            step = np.median(np.diff(up)) if len(up) > 2 else float('nan')
            print('  %2d: %d notes, step %.3f s, gate %.3f s (%.0f%%)' % (dv, len(up), step, np.median(lens[:-1]) if len(lens) > 1 else float('nan'), 100 * (np.median(lens[:-1]) if len(lens) > 1 else float('nan')) / step))
    elif what == 'swing':
        print('Swing value -> the two alternating intervals (s)')
        for sv in (14, 32, 48, 64, 80, 96, 114):
            t, *_ = onsets(take(outdir, 'swing_%d' % sv, dict(arp_swing=sv, **PLUCK), [48], 2.5))
            d = np.diff(t)
            print('  %3d: %.4f / %.4f (first share %.1f%%)' % (sv, np.median(d[0::2]), np.median(d[1::2]), 100 * np.median(d[0::2]) / (np.median(d[0::2]) + np.median(d[1::2]))))
    elif what == 'modes':
        names = ['UP', 'DOWN', 'ALT', 'RAND', '#UP', '#DWN', '#ALT']
        print('Mode, Range 2, chord 48 52 55 (played in that order): the notes in order')
        for mv in range(7):
            p = os.path.join(outdir, 'mode_%d.wav' % mv)
            if not os.environ.get('P2_REANALYSE'):
                p = take(outdir, 'mode_%d' % mv, dict(arp_mode=mv, arp_range=1, arp_tempo=40, **PLUCK), [48, 52, 55], 4.0)
            t, x, r, _ = onsets(p)
            print('  %-5s %s' % (names[mv], ' '.join(str(n) for n in pitches(None, t, x, r)[:20])))


if __name__ == '__main__':
    main()
