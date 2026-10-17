#!/usr/bin/python3
# Velocity and volume laws: the amp's level against note velocity at several Amp Velocity settings, the volume
# law, and the cutoff offset against velocity at several Filter Velocity settings (self-oscillating filter).
# usage: vel_session.py <outdir> amp|volume|filter
import os, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from fenv_session import cutoff_steps
from selfosc import track

RATE = 192000


def take(outdir, tag, sound, note, velocity, seconds=1.2):
    p2rig.set_sound(sound)
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    cap = p2rig.capture(path, seconds + 1.2, RATE)
    time.sleep(0.7)
    p2rig.send(*p2rig.note_items(note, seconds, velocity))
    cap.communicate()
    return path


def level(path):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    i = np.flatnonzero(np.abs(x) > max(np.abs(x).max() * 0.05, 1e-5))
    if len(i) == 0:
        return -150.0
    s = x[i[0] + int(0.3 * r):i[0] + int(0.9 * r)]
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12)


def osc_steps(path):
    w = wave.open(path); r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    tr = track(x, r, hop_s=0.01, n_win=16384)
    ok = tr[:, 1] > 1e-3
    return float(np.median(cutoff_steps(tr[ok, 0][5:-5]))) if ok.sum() > 12 else float('nan')


def main():
    outdir, what = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    vels = (1, 16, 32, 64, 96, 127)
    if what == 'amp':
        print('level (dBFS) against velocity %s, per Amp Velocity setting (saw, filter open, volume 40)' % (vels,))
        for av in (64, 80, 96, 127, 32, 0):
            row = [level(take(outdir, 'ampvel_%d_v%d' % (av, v), dict(volume=40, vca_velocity=av), 60, v)) for v in vels]
            print('  %3d %s' % (av, ' '.join('%7.1f' % l for l in row)))
    elif what == 'volume':
        print('level (dBFS) against Volume (velocity 100, amp velocity 64)')
        row = []
        for vol in (0, 8, 16, 24, 32, 40, 48, 64, 80, 96, 112, 127):
            row.append('%d:%.1f' % (vol, level(take(outdir, 'volume_%d' % vol, dict(volume=vol), 60, 100))))
        print('  ' + ' '.join(row))
    elif what == 'filter':
        print('cutoff steps against velocity %s, per Filter Velocity (self-oscillating, base cutoff 40)' % (vels,))
        for fv in (64, 80, 96, 127, 32):
            row = [osc_steps(take(outdir, 'fvel_%d_v%d' % (fv, v), dict(osc1_level=0, resonance=127, cutoff=40, volume=40, vcf_velocity=fv), 60, v)) - 40.0 for v in vels]
            print('  %3d %s' % (fv, ' '.join('%+7.2f' % st for st in row)))


if __name__ == '__main__':
    main()
