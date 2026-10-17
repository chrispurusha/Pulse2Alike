#!/usr/bin/python3
# The paraphonic voice fade (Env A Fade): in PARA-8, note 36 held throughout keeps the amp envelope open while
# note 60 plays for 1 s; note 61's fundamental over time is its voice fading in and out.
# usage: fade_session.py <outdir>
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

RATE = 192000
FADES = tuple(int(v) for v in os.environ.get("P2_FADES", "0,20,40,64,83,100,127").split(","))
ENV_A, ENV_R = 60, int(os.environ.get("P2_FADE_ENV_R", "70"))         # the voice fade borrows the amp envelope's times
HELD_HZ, PLAYED_HZ = 65.406, 277.183   # 61, not a harmonic of 36


def capture(outdir, fade):
    p2rig.set_sound(dict(osc1_shape=8, osc1_level=100, osc1_fade=fade, volume=40, enva_a=ENV_A, enva_r=ENV_R))
    time.sleep(0.3)
    path = os.path.join(outdir, 'fade%d_a%d_r%d.wav' % (fade, ENV_A, ENV_R))
    ch = p2rig.CHANNEL - 1
    cap = p2rig.capture(path, 8.0, RATE)
    time.sleep(0.8)
    p2rig.send(p2rig.hexmsg(0x90 | ch, 36, 100), 'sleep:500', p2rig.hexmsg(0x90 | ch, 61, 100), 'sleep:1000',
               p2rig.hexmsg(0x80 | ch, 61, 0), 'sleep:5000', p2rig.hexmsg(0x80 | ch, 36, 0))
    cap.communicate()
    return path


def track(path, hz, hop=0.01, win=0.12):
    x2, r = read(path)
    x = x2[:, 0]
    n, h = int(win * r), int(hop * r)
    w = np.hanning(n)
    t = np.arange(n) / r
    ref = np.exp(-2j * np.pi * hz * t) * w
    amp = np.array([abs(np.sum(x[i:i + n] * ref)) * 2 / w.sum() for i in range(0, len(x) - n, h)])
    return np.arange(len(amp)) * hop + win / 2, 20 * np.log10(amp + 1e-9)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    res = {}
    for fade in FADES:
        p = capture(outdir, fade)
        t, held = track(p, HELD_HZ)
        _, played = track(p, PLAYED_HZ)
        on = t[np.flatnonzero(held > held.max() - 20)[0]] + 0.5        # the played note, 0.5 s after the held one
        top = np.median(played[(t > on + 0.6) & (t < on + 0.95)])
        rise = t[np.flatnonzero((t > on - 0.05) & (played > top - 3))[0]] - on
        after = (t > on + 1.0)
        drop = {d: (t[np.flatnonzero(after & (played < top - d))[0]] - (on + 1.0)) if np.any(after & (played < top - d)) else None
                for d in (3, 10, 20, 40)}
        res[fade] = dict(rise_to_minus3=rise, release=drop, level=top)
        print('fade %3d: rises to -3 dB in %.3f s; after release -3/-10/-20/-40 dB at %s s'
              % (fade, rise, ' / '.join('%.3f' % v if v is not None else '-' for v in drop.values())))
    json.dump(res, open(os.path.join(outdir, 'fade.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
