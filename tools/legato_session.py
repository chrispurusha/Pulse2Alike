#!/usr/bin/python3
# Legato on the instrument and the engine: 48 held, 55 pressed at 0.5 s and let go at 1.0 s, 48 let go at 1.5 s.
# (1) each glide mode at Glide Rate 70: the pitch every 50 ms; (2) each amp envelope trigger with a quick decay to a
# low sustain: the level every 50 ms (a restart shows as a jump at 0.5 or 1.0 s).  usage: legato_session.py
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/legato'
CH = p2rig.CHANNEL - 1
GLIDES = ('OFF', 'NORM', 'FNGR', 'FNON', 'FOFF')
TRIGS = ('SNG1', 'SNG2', 'RET1', 'RET2', 'RET3')


def play(sound, path):
    p2rig.set_sound(sound)
    time.sleep(0.3)
    cap = p2rig.capture(path, 2.6, 192000)
    time.sleep(0.8)
    on, off = 0x90 | CH, 0x80 | CH
    p2rig.send(p2rig.hexmsg(on, 48, 100), 'sleep:500', p2rig.hexmsg(on, 55, 100), 'sleep:500', p2rig.hexmsg(off, 55, 0),
               'sleep:500', p2rig.hexmsg(off, 48, 0))
    cap.communicate()


def render(over, path):
    subprocess.run(['./p2render', '-', '48:0:1.5,55:0.5:0.5', '1.5', '0.3', path, '192000', *sq.ENGINE_BASE, 'osc1shape=1',
                    'osc1level=127', 'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40', *over],
                   check=True, capture_output=True)


def track(path, gain, what):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    out = []
    for t0 in np.arange(0.0, 1.5, 0.05):
        s = x[on + int(t0 * r):on + int((t0 + 0.05) * r)]
        if what == 'pitch':
            z = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0))
            out.append(12 * np.log2((r / np.median(np.diff(z))) / 130.81) if len(z) > 2 else np.nan)
        else:
            out.append(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9))
    return np.array(out)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = os.environ.get('TMPDIR', '/tmp')
    print('pitch over 0-1.5 s in semitones over 48, every 0.1 s (55 pressed at 0.5, let go at 1.0)')
    for i, g in enumerate(GLIDES):
        hw = os.path.join(OUT, 'hw_glide_%s.wav' % g)
        if not os.path.exists(hw):
            play(dict(osc1_shape=1, osc1_level=127, cutoff=127, volume=40, glide_rate=70, glide_mode=i), hw)
        p2 = os.path.join(d, 'leg.wav')
        render(['gliderate=70', 'glidemode=%d' % i], p2)
        h, e = track(hw, 1.0, 'pitch'), track(p2, 10.0, 'pitch')
        print('%-5s hw %s\n      p2 %s' % (g, ' '.join('%5.1f' % v for v in h[::2]), ' '.join('%5.1f' % v for v in e[::2])))
    print('level (dB) every 0.1 s, envelope A decay 30 sustain 30')
    for i, tr in enumerate(TRIGS):
        hw = os.path.join(OUT, 'hw_trig_%s.wav' % tr)
        if not os.path.exists(hw):
            play(dict(osc1_shape=1, osc1_level=127, cutoff=127, volume=40, enva_d=30, enva_s=30, enva_trigger=i), hw)
        p2 = os.path.join(d, 'leg.wav')
        render(['ampenvdecay=30', 'ampenvsustain=30', 'ampenvtrigger=%d' % i], p2)
        h, e = track(hw, 1.0, 'level'), track(p2, 10.0, 'level')
        print('%-5s hw %s\n      p2 %s' % (tr, ' '.join('%5.0f' % v for v in h[::2]), ' '.join('%5.0f' % v for v in e[::2])))
