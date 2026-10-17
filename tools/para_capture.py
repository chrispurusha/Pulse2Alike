#!/usr/bin/python3
# Paraphonic captures: a chord held in PARA-8 or PARA-4, then which fundamentals sound and at what level, and a
# single note's waveform. usage: para_capture.py <outdir> <mode 8|9> <notes,comma,separated> [seconds]
import json, os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

RATE = 192000


def capture(outdir, mode, notes, seconds):
    os.makedirs(outdir, exist_ok=True)
    p2rig.set_sound(dict(osc1_shape=mode, osc1_level=100, volume=40))
    time.sleep(0.3)
    tag = 'para%d_%s' % (mode, '-'.join(str(n) for n in notes))
    path = os.path.join(outdir, tag + '.wav')
    ch = p2rig.CHANNEL - 1
    items = []
    for n in notes:
        items += [p2rig.hexmsg(0x90 | ch, n, 100), 'sleep:20']
    items += ['sleep:%d' % int(seconds * 1000)] + [p2rig.hexmsg(0x80 | ch, n, 0) for n in notes]
    cap = p2rig.capture(path, seconds + 1.8, RATE)
    time.sleep(0.8)
    p2rig.send(*items)
    cap.communicate()
    json.dump({'mode': mode, 'notes': notes}, open(path[:-4] + '.json', 'w'))
    return path


def analyse(path, notes):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    on = np.flatnonzero(np.abs(x) > 1e-3)[0]
    s = x[on + int(0.5 * r):on + int(1.5 * r)]
    win = np.hanning(len(s))
    X = np.abs(np.fft.rfft(s * win)) * 2 / win.sum()
    f = np.fft.rfftfreq(len(s), 1 / r)
    out = []
    for n in notes:
        hz = 440 * 2 ** ((n - 69) / 12)
        k = np.argmin(np.abs(f - hz))
        out.append((n, 20 * np.log10(X[k - 2:k + 3].max() + 1e-12)))
    return out, 20 * np.log10(np.sqrt(np.mean(s ** 2)))


if __name__ == '__main__':
    outdir, mode = sys.argv[1], int(sys.argv[2])
    notes = [int(n) for n in sys.argv[3].split(',')]
    seconds = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
    p = capture(outdir, mode, notes, seconds)
    levels, rms = analyse(p, notes)
    print('PARA-%s %s: rms %.1f dBFS; fundamental levels: %s' % ('8' if mode == 8 else '4', notes, rms,
          ' '.join('%d:%.1f' % lv for lv in levels)))
