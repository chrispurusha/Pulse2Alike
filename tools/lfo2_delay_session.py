#!/usr/bin/python3
# LFO 2's Delay: LFO 2 (speed 70, ~9.75 Hz) on osc 1's pitch, a note held 12 s, Delay 0..127; the vibrato's depth
# envelope read off the pitch track - how long nothing moves, and how long it takes to reach full depth.
# usage: lfo2_delay_session.py [capture|analyse] [render]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/lfo2'
DELAYS = (0, 8, 16, 30, 45, 60, 75, 90, 105, 127)
F0, HOLD = 130.8128, 12.0


def capture():
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    for dly in DELAYS:
        hw = os.path.join(OUT, 'hw_delay%d.wav' % dly)
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(osc1_shape=0, osc1_pw=64, osc1_level=127, osc2_level=0, cutoff=127, volume=40))
        p2rig.send(*[p2rig.hexmsg(ch, c, v) for c, v in ((26, 70), (27, dly), (108, 4), (109, 74), (110, 1))])
        time.sleep(0.3)
        cap = p2rig.capture(hw, HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(48, HOLD))
        cap.communicate()
        p2rig.send(p2rig.hexmsg(ch, 108, 0))


def render(dly, path):
    subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render'), '-', '48', str(HOLD), '0.2', path, '192000',
                    *sq.ENGINE_BASE, 'osc1shape=0', 'osc1pulsewidth=64', 'osc1level=127', 'osc2level=0', 'osc3level=0',
                    'noiselevel=0', 'cutoff=127', 'volume=40', 'lfo2speed=70', 'lfo2delay=%d' % dly, 'mod1source=4',
                    'mod1amount=74', 'mod1target=1'], check=True, capture_output=True)


def depth(path, gain):
    """Vibrato depth (cents, half peak-to-peak per LFO cycle) against time since the note."""
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    k = max(1, int(r / 600))
    y = np.convolve(np.convolve(x[on:] - x[on:].mean(), np.ones(k) / k, 'same'), np.ones(k) / k, 'same')
    z = np.flatnonzero((y[:-1] < 0) & (y[1:] >= 0)).astype(float)
    zi = z.astype(int)
    z = z + (-y[zi] / (y[zi + 1] - y[zi]))
    t = z[1:] / r
    c = 1200 * np.log2((r / np.diff(z)) / F0)
    edges = np.arange(0.0, HOLD - 0.2, 0.1025)               # one LFO cycle a bin
    d = []
    for a in edges:
        m = (t >= a) & (t < a + 0.1025)
        d.append((c[m].max() - c[m].min()) / 2 if m.sum() > 2 else 0.0)
    return edges, np.array(d)


def summary(edges, d):
    full = np.median(d[-20:])
    def at(frac):
        i = np.flatnonzero(d >= frac * full)
        return edges[i[0]] if len(i) else float('nan')
    return 'full %4.0f c  10%% at %5.2f s  50%% at %5.2f s  90%% at %5.2f s' % (full, at(0.1), at(0.5), at(0.9))


def analyse(with_render):
    for dly in DELAYS:
        line = 'delay %3d  hw %s' % (dly, summary(*depth(os.path.join(OUT, 'hw_delay%d.wav' % dly), 1.0)))
        if with_render:
            p = os.path.join(os.environ['TMPDIR'], 'l2d.wav')
            render(dly, p)
            line += ' | p2 %s' % summary(*depth(p, 10.0))
        print(line)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if mode in ('capture', 'both'):
        capture()
    if mode in ('analyse', 'both'):
        analyse('render' in sys.argv)
