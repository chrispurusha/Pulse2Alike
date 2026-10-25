#!/usr/bin/python3
# A library sound's level over time, instrument and engine, with CC overrides per variant (patch_variant.py's
# capture): 30 ms windows through the first 0.3 s, then 0.2 s, then 0.1 s after the release.
# usage: patch_trace.py <nnn> <note> <variant>=<cc:value,...>[;<renderer overrides>] ...
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from patch_variant import OUT, PATCHES
from patch_validate import read, onset

HOLD = 2.0
TIMES = np.concatenate([np.arange(0, 0.3, 0.03), np.arange(0.3, HOLD, 0.2), np.arange(HOLD, HOLD + 0.7, 0.1)])


def trace(path, gain):
    x, r = read(path)
    x = x * gain
    s0 = onset(x, r)
    return np.array([10 * np.log10(np.mean(x[s0 + int(t * r):s0 + int((t + 0.03) * r)] ** 2) + 1e-20) for t in TIMES])


def main():
    n, note = int(sys.argv[1]), int(sys.argv[2])
    syx = os.path.join(PATCHES, 'fixedlfo_%03d.syx' % n)
    ch = 0xB0 | (p2rig.CHANNEL - 1)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    print('t          ' + ' '.join('%5.2f' % t for t in TIMES))
    for arg in sys.argv[3:]:
        tag, spec = arg.split('=', 1)
        ccs, _, ren = spec.partition(';')
        pairs = [tuple(int(v) for v in kv.split(':')) for kv in ccs.split(',') if kv]
        hw = os.path.join(OUT, 'trace_%03d_n%d_%s.wav' % (n, note, tag))
        for attempt in range(2):                           # the first take after a sound change can miss its note
            if os.path.exists(hw) and np.abs(read(hw)[0]).max() > 0.003:
                break
            p2rig.send(open(syx, 'rb').read().hex(), 'sleep:400', p2rig.hexmsg(ch, 1, 0), *[p2rig.hexmsg(ch, c, v) for c, v in pairs])
            time.sleep(0.6)
            cap = p2rig.capture(hw, HOLD + 2.0, 192000)
            time.sleep(0.9)
            p2rig.send(*p2rig.note_items(note, HOLD))
            cap.communicate()
        p2 = os.path.join(os.environ['TMPDIR'], 'trace.wav')
        subprocess.run([render, syx, str(note), str(HOLD), '1.0', p2, '96000', *[o for o in ren.split(',') if o]],
                       check=True, capture_output=True)
        h, e = trace(hw, 1.0), trace(p2, 10.0)
        print('%-10s %s' % (tag + ' hw', ' '.join('%5.1f' % v for v in h)))
        print('%-10s %s' % ('   p2-hw', ' '.join('%+5.1f' % v for v in e - h)))


if __name__ == '__main__':
    main()
