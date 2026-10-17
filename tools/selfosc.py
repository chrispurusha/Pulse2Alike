#!/usr/bin/python3
# The filter's self-oscillation against cutoff (filter plan step 1): resonance up, no input, a note held, the
# cutoff stepped every STEP_S within one capture; per step, the oscillation's frequency and level.
# usage: selfosc.py <outdir> <tag> [first last step] [name=value ...]
import json, os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

RATE = 192000
STEP_S = 0.6
SEND_GAP_S = 0.002           # midisend pauses this long after every message, so each step lasts STEP_S + this
NOTE = 60
BASE = dict(osc1_level=0, osc3_shape=3, osc3_level=0, resonance=127, volume=40)


def run(outdir, tag, cutoffs, overrides, stepped='cutoff'):
    os.makedirs(outdir, exist_ok=True)
    sound = dict(BASE); sound.update(overrides); sound[stepped] = cutoffs[0]
    p2rig.set_sound(sound)
    path = os.path.join(outdir, tag + '.wav')
    items = [p2rig.hexmsg(0x90 | (p2rig.CHANNEL - 1), NOTE, 100)]
    for c in cutoffs:
        items += [p2rig.hexmsg(0xB0 | (p2rig.CHANNEL - 1), p2rig.CC[stepped], c), 'sleep:%d' % int(STEP_S * 1000)]
    items.append(p2rig.hexmsg(0x80 | (p2rig.CHANNEL - 1), NOTE, 0))
    cap = p2rig.capture(path, 1.5 + len(cutoffs) * (STEP_S + SEND_GAP_S) + 0.5, RATE)
    time.sleep(1.0)
    p2rig.send(*items)
    cap.communicate()
    json.dump({'sound': sound, 'stepped': stepped, 'values': cutoffs, 'step_s': STEP_S}, open(path[:-4] + '.json', 'w'), indent=1)
    return path


def track(x, r, hop_s=0.01, n_win=32768):
    """Frequency every hop_s from the spectral peak (parabolic on log magnitude), and rms."""
    win = np.hanning(n_win)
    hop = int(hop_s * r)
    out = []
    for a in range(0, len(x) - n_win, hop):
        s = x[a:a + n_win]
        X = np.abs(np.fft.rfft((s - s.mean()) * win, 4 * n_win))
        k = int(np.argmax(X[8:])) + 8
        a1, b1, c1 = np.log(X[k - 1:k + 2] + 1e-30)
        out.append(((k + 0.5 * (a1 - c1) / (a1 - 2 * b1 + c1)) * r / (4 * n_win), np.sqrt(np.mean(s ** 2))))
    return np.array(out)


# notes: PLATEAUS, NOT THE CLOCK. A step is found where the tracked frequency holds still, so neither the
# capture's late start nor midisend's per-message gap can label a step with its neighbour's value.
def analyse(path, cutoffs, min_s=0.25):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    tr = track(x, r)
    semis = 12 * np.log2(np.maximum(tr[:, 0], 1.0))
    loud = tr[:, 1] > 10 ** (-50 / 20)
    plateaus, start = [], None
    for i in range(1, len(tr)):
        steady = loud[i] and loud[i - 1] and abs(semis[i] - semis[i - 1]) < 0.1
        if steady and start is None:
            start = i - 1
        elif not steady and start is not None:
            if (i - start) * 0.01 >= min_s:
                plateaus.append((start, i))
            start = None
    if start is not None and (len(tr) - start) * 0.01 >= min_s:
        plateaus.append((start, len(tr)))
    if len(plateaus) != len(cutoffs):
        print('warning: %d plateaus for %d cutoffs - steps that do not move the frequency merge' % (len(plateaus), len(cutoffs)))
    rows = []
    for c, (a, b) in zip(cutoffs, plateaus):
        mid = slice(a + (b - a) // 4, b - (b - a) // 4)
        f = float(np.median(tr[mid, 0]))
        x0 = int((a + (b - a) // 4) * 0.01 * r)
        s = x[x0:x0 + int(0.2 * r)]; s = s - s.mean()
        win = np.hanning(len(s)); X = np.abs(np.fft.rfft(s * win)); df = r / len(s)
        h = lambda m: X[int(round(m * f / df))] if m * f < r / 2 else 0.0
        h1 = h(1)
        rows.append((c, f, 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12),
                     20 * np.log10(h(2) / h1 + 1e-12), 20 * np.log10(h(3) / h1 + 1e-12)))
    return rows


if __name__ == '__main__':
    outdir, tag = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    nums = [a for a in rest if '=' not in a]
    first, last, step = (int(v) for v in nums) if nums else (0, 127, 1)
    cutoffs = list(range(first, last + 1, step))
    ov = {k: int(v) for k, v in (a.split('=') for a in rest if '=' in a)}
    path = run(outdir, tag, cutoffs, ov)
    rows = analyse(path, cutoffs)
    np.savetxt(path[:-4] + '_osc.csv', np.array(rows), delimiter=',', fmt='%.4f', header='cutoff,hz,rms_dbfs,h2_db,h3_db')
    prev = None
    for c, f, rms, h2, h3 in rows:
        st = '' if prev is None else '%+.3f' % (12 * np.log2(f / prev[1]) / (c - prev[0]))
        print('%4d %10.2f Hz %7.1f dBFS  H2 %6.1f  H3 %6.1f  %s' % (c, f, rms, h2, h3, st))
        prev = (c, f)
