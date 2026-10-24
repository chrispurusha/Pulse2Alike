#!/usr/bin/python3
# Polarity audit: each source alone (filter open, note 48) on the instrument and the engine, one cycle folded and the
# engine's matched to the instrument's by cross-correlation with either sign; also EXT IN against the signal sent.
# usage: polarity_session.py [analyse]
import os, subprocess, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig
import squash_session as sq
from osc_analyse import read

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/polarity'
NOTE, HOLD, F0 = 48, 2.0, 130.8128
SILENT = dict(osc1_level=0, osc2_level=0, osc3_level=0, noise=0, cutoff=127, resonance=0, volume=40)
# (CC settings, engine overrides)
CASES = {
    'o1_pwm':  (dict(osc1_shape=0, osc1_pw=64, osc1_level=127), ['osc1shape=0', 'osc1pulsewidth=64', 'osc1level=127']),
    'o1_saw':  (dict(osc1_shape=1, osc1_level=127), ['osc1shape=1', 'osc1level=127']),
    'o1_tri':  (dict(osc1_shape=2, osc1_level=127), ['osc1shape=2', 'osc1level=127']),
    'o1_apw':  (dict(osc1_shape=3, osc1_pw=64, osc1_level=127), ['osc1shape=3', 'osc1pulsewidth=64', 'osc1level=127']),
    'o1_para8': (dict(osc1_shape=8, osc1_pw=64, osc1_level=127), ['osc1shape=8', 'osc1pulsewidth=64', 'osc1level=127']),
    'o2_pwm':  (dict(osc2_shape=0, osc2_pw=64, osc2_level=127), ['osc2shape=0', 'osc2pulsewidth=64', 'osc2level=127']),
    'o2_saw':  (dict(osc2_shape=1, osc2_level=127), ['osc2shape=1', 'osc2level=127']),
    'o2_tri':  (dict(osc2_shape=2, osc2_level=127), ['osc2shape=2', 'osc2level=127']),
    'o2_x3w0': (dict(osc2_shape=3, osc2_pw=0, osc2_level=127, osc3_shape=0), ['osc2shape=3', 'osc2pulsewidth=0', 'osc2level=127', 'osc3shape=0']),
    'o3_sqr':  (dict(osc3_shape=0, osc3_level=127), ['osc3shape=0', 'osc3level=127']),
    'o3_saw':  (dict(osc3_shape=1, osc3_level=127), ['osc3shape=1', 'osc3level=127']),
    'o3_tri':  (dict(osc3_shape=2, osc3_level=127), ['osc3shape=2', 'osc3level=127']),
}
BASE_ENGINE = sq.ENGINE_BASE + ['osc1level=0', 'osc2level=0', 'osc3level=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40']


def ext_signal(path, rate=192000, seconds=3.5, hz=100.0):
    """A deliberately lopsided wave (fundamental plus its 2nd harmonic in phase): its sign shows at a glance."""
    t = np.arange(int(rate * seconds)) / rate
    x = 0.03 * (np.sin(2 * np.pi * hz * t) + 0.5 * np.sin(2 * np.pi * 2 * hz * t + np.pi / 2))
    w = wave.open(path, 'wb')
    w.setnchannels(1)
    w.setsampwidth(4)
    w.setframerate(rate)
    w.writeframes((x * 2 ** 31).astype('<i4').tobytes())
    w.close()
    return x


def capture():
    os.makedirs(OUT, exist_ok=True)
    for name, (cc, _) in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(SILENT, **cc))
        time.sleep(0.3)
        cap = p2rig.capture(hw, HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()
    hw = os.path.join(OUT, 'hw_ext.wav')
    if not os.path.exists(hw):
        sig = os.path.join(OUT, 'ext_signal.wav')
        ext_signal(sig)
        p2rig.set_sound(dict(SILENT, osc3_shape=3, osc3_level=127))
        time.sleep(0.3)
        cap = p2rig.capture(hw, 4.0, 192000)
        time.sleep(0.6)
        play = subprocess.Popen([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'play'), '--device', 'Fireface',
                                 '--channels', str(p2rig.EXT_OUT_CHANNEL), '--file', sig])
        p2rig.send(*p2rig.note_items(NOTE, 3.0))
        play.wait()
        cap.communicate()


def cycle(path, gain, f0=F0):
    x2, r = read(path)
    x = (x2[:, 0] if x2.ndim > 1 else x2) * gain
    on = np.flatnonzero(np.abs(x) > np.abs(x).max() * 0.05)[0]
    s = x[on + int(0.5 * r):on + int(1.5 * r)]
    s = s - s.mean()
    period = r / f0
    n = int(len(s) / period) - 1
    grid = np.arange(256) * period / 256
    cyc = np.array([np.interp(grid + k * period, np.arange(len(s)), s) for k in range(n)])
    ref = cyc[0]
    al = [np.roll(c, -int(np.argmax([np.dot(ref, np.roll(c, -j)) for j in range(0, 256, 2)]) * 2)) for c in cyc]
    return np.mean(al, axis=0)


def match(a, b):
    """The best circular correlation of b against a, with b as is and inverted: (corr, sign)."""
    a = (a - a.mean()) / (np.std(a) + 1e-12)
    b = (b - b.mean()) / (np.std(b) + 1e-12)
    best = max((np.dot(a, np.roll(s * b, j)) / len(a), s) for s in (1, -1) for j in range(256))
    return best


if __name__ == '__main__':
    if 'analyse' not in sys.argv:
        capture()
    d = os.environ.get('TMPDIR', '/tmp')
    print('%-10s %s' % ('source', 'engine vs instrument: best correlation, and its sign (+1 = same polarity)'))
    for name, (_, ov) in CASES.items():
        p2 = os.path.join(d, 'pol_%s.wav' % name)
        subprocess.run(['./p2render', '-', str(NOTE), str(HOLD), '0.3', p2, '192000', *BASE_ENGINE, *ov], check=True, capture_output=True)
        a, b = cycle(os.path.join(OUT, 'hw_%s.wav' % name), 1.0), cycle(p2, 10.0)
        c, sgn = match(a, b)
        c2, _ = max((np.dot((a - a.mean()) / np.std(a), np.roll(-sgn * (b - b.mean()) / np.std(b), j)) / len(a), 0) for j in range(256))
        print('%-10s %+.3f  sign %+d   (the other sign at best %+.3f)%s' % (name, c, sgn, c2, '   <-- INVERTED' if sgn < 0 else ''))
    # EXT: the output against the signal sent, both at 100 Hz
    sent = ext_signal(os.path.join(d, 'sent.wav'))
    a = cycle(os.path.join(d, 'sent.wav'), 1.0, 100.0)
    b = cycle(os.path.join(OUT, 'hw_ext.wav'), 1.0, 100.0)
    c, sgn = match(a, b)
    print('%-10s %+.3f  sign %+d  (the instrument against the signal sent into EXT IN)' % ('ext', c, sgn))
