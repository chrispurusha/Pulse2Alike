#!/usr/bin/python3
# The mod matrix's scaling per target (todo, Engine): LFO 1 square at a slow speed through mod slot 1, so the
# target flips between two steady values; the difference against the amount gives the target's scale.
# usage: mod_targets.py <outdir> pitch|pw|level
import os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import refine_f0

RATE = 192000
LFO_SPEED, LFO_SQR = 16, 3          # 0.43 Hz: 1.15 s on each side of the square
TGT = {'pitch': 0, 'pw': 4, 'level': 6}


def take(outdir, tag, target, amount, sound):
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    p2rig.set_sound(dict(volume=40, **sound))
    p2rig.send(p2rig.hexmsg(ch, p2rig.CC_LFO1_SPEED, LFO_SPEED), p2rig.hexmsg(ch, p2rig.CC_LFO1_SHAPE, LFO_SQR),
               p2rig.hexmsg(ch, 108, 1), p2rig.hexmsg(ch, 110, TGT[target]), p2rig.hexmsg(ch, 109, amount))
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, 6.0, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(60, 5.0))
    cap.communicate()
    return path


def windows(path, n=40):
    """Short windows across the take, for plateau statistics."""
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    on = np.flatnonzero(np.abs(x) > 1e-3)[0]
    span = int(0.1 * r)
    return [x[on + int(0.2 * r) + i * span: on + int(0.2 * r) + (i + 1) * span] for i in range(n)], r


def two_levels(values):
    v = np.sort(np.array(values))
    k = int(np.argmax(np.diff(v))) + 1          # the biggest gap splits the two plateaus
    return np.median(v[:k]), np.median(v[k:])


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for a in (68, 72, 80, 96, 112):
        if what == 'pitch':
            segs, r = windows(take(outdir, 'pitch_%d' % a, 'pitch', a, dict(osc1_shape=1)))
            f = [refine_f0(s - s.mean(), r, 261.626 * 2 ** (0.0)) if False else None for s in segs]
            f = []
            for s in segs:
                X = np.abs(np.fft.rfft((s - s.mean()) * np.hanning(len(s)), 1 << 20))
                fr = np.fft.rfftfreq(1 << 20, 1 / r)
                m = (fr > 100) & (fr < 1200)
                f.append(fr[m][np.argmax(X[m])])
            lo, hi = two_levels(12 * np.log2(np.array(f) / 261.626))
            print('pitch  amount %3d: %+.3f / %+.3f semitones (swing %.3f)' % (a, lo, hi, hi - lo))
        elif what == 'pw':
            segs, r = windows(take(outdir, 'pw_%d' % a, 'pw', a, dict(osc1_shape=0, osc1_pw=64)))
            duty = []
            for s in segs:
                ph = (np.arange(len(s)) * 261.626 / r) % 1
                b = np.minimum((ph * 256).astype(int), 255)
                cyc = np.bincount(b, s, 256) / np.maximum(np.bincount(b, None, 256), 1)
                duty.append(np.mean(cyc > (cyc.max() + cyc.min()) / 2))
            lo, hi = two_levels(duty)
            print('pw     amount %3d: duty %.4f / %.4f' % (a, lo, hi))
        elif what == 'level':
            segs, r = windows(take(outdir, 'level_%d' % a, 'level', a, dict(osc1_shape=1, osc1_level=64)))
            lv = [20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12) for s in segs]
            lo, hi = two_levels(lv)
            print('level  amount %3d: %.2f / %.2f dBFS' % (a, lo, hi))


if __name__ == '__main__':
    main()
