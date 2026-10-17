#!/usr/bin/python3
# Envelope captures (amp envelope, ENVA): osc 1 saw at note 96 through the open filter, the VCA following the
# envelope; the output's envelope is read by rectifying and smoothing over 1 ms.
# usage: env_capture.py <outdir> <stage: attack|decay|release|sustain> <value> [hold_s] [tail_s]
import json, os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

RATE = 192000
NOTE = 96


def settings(stage, v):
    env = dict(enva_a=0, enva_d=0, enva_s=127, enva_r=0)
    if stage == 'attack':
        env['enva_a'] = v
    elif stage == 'decay':
        env.update(enva_d=v, enva_s=0)
    elif stage == 'release':
        env['enva_r'] = v
    elif stage == 'sustain':
        env['enva_s'] = v
    return env


def capture(outdir, stage, v, hold, tail):
    os.makedirs(outdir, exist_ok=True)
    p2rig.set_sound(dict(volume=40, **settings(stage, v)))
    time.sleep(0.3)
    path = os.path.join(outdir, '%s_%d.wav' % (stage, v))
    cap = p2rig.capture(path, 1.0 + hold + tail, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(NOTE, hold))
    cap.communicate()
    json.dump({'stage': stage, 'value': v, 'hold_s': hold, 'tail_s': tail, 'note': NOTE}, open(path[:-4] + '.json', 'w'))
    return path


def envelope(path):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    n = r // 1000
    e = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, 'same'))[::n // 4]   # 4 points per ms
    return e, 4000.0


if __name__ == '__main__':
    outdir, stage, v = sys.argv[1], sys.argv[2], int(sys.argv[3])
    hold = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
    tail = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
    p = capture(outdir, stage, v, hold, tail)
    e, fs = envelope(p)
    top = np.percentile(e, 99.5)
    db = 20 * np.log10(e / top + 1e-9)
    on = np.flatnonzero(db > -60)
    print('%s %d: signal from %.3f s to %.3f s; peak %.1f dBFS' % (stage, v, on[0] / fs, on[-1] / fs, 20 * np.log10(top)))
