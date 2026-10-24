#!/usr/bin/python3
# Where does an oscillator squash the noise? The test sound (p2rig) with osc 1 a triangle and the noise at 104, osc 1's
# level swept at a few cutoffs and volumes, on the instrument and the engine; the noise read between note 48's harmonics,
# against the noise alone at the same setting.  usage: squash_session.py [capture|analyse] [take-tag-prefix]
import os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/squash'
NOTE, F0, HOLD, NOISE = 48, 130.8128, 2.5, 104
LEVELS = (0, 60, 90, 120, 127)
SETTINGS = {'c127_v40': (127, 0, 40), 'c64_v40': (64, 0, 40), 'c40_v40': (40, 0, 40),
            'c127_v100': (127, 0, 100), 'c64_r41_v40': (64, 41, 40)}
BANDS = ((100, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000))
WINDOW = (0.4, 2.2)
ENGINE_BASE = ['osc1shape=2', 'osc1semitone=0', 'osc1detune=64', 'osc1keytrack=1', 'osc2level=0', 'osc3level=0',
               'filtertype=0', 'filterenvamount=64', 'filterkeytrack=64', 'filtervelocity=64', 'drive=0', 'drivecurve=0',
               'pan=64', 'ampvelocity=64', 'filterenvattack=0', 'filterenvdecay=0', 'filterenvsustain=127', 'filterenvrelease=0',
               'filterenvloop=0', 'filterenvtrigger=0', 'ampenvattack=0', 'ampenvdecay=0', 'ampenvsustain=127', 'ampenvrelease=0',
               'ampenvloop=0', 'ampenvtrigger=0', 'glidemode=0', 'arpactive=0', 'unisondetune=0', 'osc1envafade=0', 'osc2envafade=0']


def cases():
    for tag, (cutoff, res, vol) in SETTINGS.items():
        for level in LEVELS:
            yield '%s_o%d_n%d' % (tag, level, NOISE), cutoff, res, vol, level, NOISE
        yield '%s_o127_n0' % tag, cutoff, res, vol, 127, 0


def capture(only=''):
    os.makedirs(OUT, exist_ok=True)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2render')
    for name, cutoff, res, vol, level, noise in cases():
        if not name.startswith(only):
            continue
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        p2rig.set_sound(dict(osc1_shape=2, osc1_level=level, noise=noise, cutoff=cutoff, resonance=res, volume=vol))
        time.sleep(0.3)
        cap = p2rig.capture(hw, HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()
        subprocess.run([render, '-', str(NOTE), str(HOLD), '0.3', os.path.join(OUT, 'p2_%s.wav' % name), '192000',
                        *ENGINE_BASE, 'osc1level=%d' % level, 'noiselevel=%d' % noise, 'cutoff=%d' % cutoff,
                        'resonance=%d' % res, 'volume=%d' % vol], check=True, capture_output=True)


def between_harmonics(path):
    x2, r = read(path)
    x = x2[:, 0] if x2.ndim > 1 else x2
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(WINDOW[0] * r):on + int(WINDOW[1] * r)]
    w = np.hanning(len(s))
    p = np.abs(np.fft.rfft((s - s.mean()) * w)) ** 2 / (w ** 2).sum()
    f = np.fft.rfftfreq(len(s), 1 / r)
    gap = np.abs(f / F0 - np.round(f / F0)) * F0 > 12.0
    return np.array([10 * np.log10(p[gap & (f >= lo) & (f < hi)].mean()) for lo, hi in BANDS]), np.abs(x).max()


def analyse():
    print('noise between the harmonics against the noise alone, dB (bands %s); [] = osc alone, below the noise by' %
          ' '.join('%d-%d' % b for b in BANDS))
    for tag in SETTINGS:
        print('\n' + tag)
        for side in ('hw', 'p2'):
            ref, _ = between_harmonics(os.path.join(OUT, '%s_%s_o0_n%d.wav' % (side, tag, NOISE)))
            oscOnly, _ = between_harmonics(os.path.join(OUT, '%s_%s_o127_n0.wav' % (side, tag)))
            print('  %s noise alone %s   osc 127 alone %s' % (side, ' '.join('%6.1f' % v for v in ref),
                                                          ' '.join('%6.1f' % v for v in oscOnly - ref)))
            for level in LEVELS[1:]:
                d, peak = between_harmonics(os.path.join(OUT, '%s_%s_o%d_n%d.wav' % (side, tag, level, NOISE)))
                print('  %s osc %3d  %s   peak %.3f' % (side, level, ' '.join('%6.1f' % v for v in d - ref), peak))


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if mode in ('capture', 'both'):
        capture(sys.argv[2] if len(sys.argv) > 2 else '')
    if mode in ('analyse', 'both'):
        analyse()
