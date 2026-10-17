#!/usr/bin/env python3
# Captures one oscillator shape at a ladder of pitches (design §5.1).
# usage: osc_capture.py <out.wav> <shape 0..2> [name=value ...] [notes=36,48,...]
# Writes <out.wav> and <out.json> naming the notes in the order played.
import json, sys, time

import p2rig

NOTES = (36, 48, 60, 72, 84, 96)
HOLD_S = 1.2
GAP_S = 0.4
RATE = 192000

out, shape = sys.argv[1], int(sys.argv[2])
overrides = {'osc1_shape': shape}
notes = NOTES
for arg in sys.argv[3:]:
    k, v = arg.split('=')
    if k == 'notes':
        notes = tuple(int(n) for n in v.split(','))
    else:
        overrides[k] = int(v)

p2rig.set_sound(overrides)
time.sleep(0.3)
seconds = 1.0 + len(notes) * (HOLD_S + GAP_S) + 0.5
proc = p2rig.capture(out, seconds, RATE)
time.sleep(1.0)
items = []
for n in notes:
    items += p2rig.note_items(n, HOLD_S) + ['sleep:%d' % int(GAP_S * 1000)]
p2rig.send(*items)
print(proc.communicate()[0].strip().splitlines()[-1])
json.dump({'notes': notes, 'hold_s': HOLD_S, 'gap_s': GAP_S, 'settings': overrides},
          open(out.rsplit('.', 1)[0] + '.json', 'w'), indent=1)
