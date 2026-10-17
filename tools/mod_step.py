#!/usr/bin/python3
# Is cutoff modulation smooth or stepped (todo, Filter)? LFO 1 saw -> cutoff through mod slot 1, the filter
# self-oscillating with no input; the oscillation's frequency is read cycle by cycle from its zero crossings.
# usage: mod_step.py <outdir> [lfo_speed] [amount] [cutoff] [seconds]
import json, os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

RATE = 192000
LFO1_SAW = 2          # LFO 1 shape list: SINE TRI SAW ...
SRC_LFO1 = 1          # mod source list: OFF LFO1 ...
TGT_CUTOFF = 10       # mod target list: PITCH OSC1 PITCH ... CUTOFF


def capture(outdir, speed, amount, cutoff, seconds):
    os.makedirs(outdir, exist_ok=True)
    p2rig.set_sound(dict(osc1_level=0, resonance=127, cutoff=cutoff, volume=40))
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    p2rig.send(p2rig.hexmsg(ch, p2rig.CC_LFO1_SHAPE, LFO1_SAW), p2rig.hexmsg(ch, p2rig.CC_LFO1_SPEED, speed),
               p2rig.hexmsg(ch, 108, SRC_LFO1), p2rig.hexmsg(ch, 110, TGT_CUTOFF), p2rig.hexmsg(ch, 109, amount))
    time.sleep(0.3)
    path = os.path.join(outdir, 'modstep_s%d_a%d_c%d.wav' % (speed, amount, cutoff))
    cap = p2rig.capture(path, seconds + 1.5, RATE)
    time.sleep(0.8)
    p2rig.send(*p2rig.note_items(60, seconds))
    cap.communicate()
    json.dump({'lfo_speed': speed, 'amount': amount, 'cutoff': cutoff}, open(path[:-4] + '.json', 'w'))
    return path


def cycle_track(path):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    x = x - np.convolve(x, np.ones(r // 5) / (r // 5), 'same')           # remove any slow offset (200 ms, so 25 Hz survives)
    i = np.flatnonzero((x[:-1] < 0) & (x[1:] >= 0))
    t = i + (-x[i] / (x[i + 1] - x[i]))                                   # interpolated rising crossings
    period = np.diff(t) / r
    return t[1:] / r, 1.0 / period


if __name__ == '__main__':
    outdir = sys.argv[1]
    speed, amount, cutoff, seconds = [int(a) for a in (sys.argv[2:5] + ['20', '100', '64'][len(sys.argv[2:5]):])] + [float(sys.argv[5]) if len(sys.argv) > 5 else 4.0]
    path = capture(outdir, speed, amount, cutoff, seconds)
    t, f = cycle_track(path)
    semis = 12 * np.log2(f / 440.0) + 69
    jumps = np.abs(np.diff(semis))
    print('cycles %d, pitch %.1f..%.1f MIDI; per-cycle change: median %.4f, 99th pct %.4f, max %.3f semitones' % (
        len(f), semis.min(), semis.max(), np.median(jumps), np.percentile(jumps, 99), jumps.max()))
    np.savetxt(path[:-4] + '_track.csv', np.column_stack([t, f]), delimiter=',', fmt='%.7f')
