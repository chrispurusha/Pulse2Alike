#!/usr/bin/python3
# The filter's response through EXT IN (design §5.2): a log sine sweep from Fireface output 6, a note held,
# both outputs captured, the response read as captured / played after aligning them. Needs numpy (/usr/bin/python3 has it).
# usage: filter_sweep.py <outdir> <tag> [name=value ...] [level_db=-30]   (names as p2rig.CC; the EXT sound is the base)
import json, os, subprocess, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

RATE = 192000
SWEEP_S = 3.0
LEVEL_DB = -30.0
F_LO, F_HI = 20.0, 40000.0
NOTE = 60
EXT_SOUND = dict(osc1_level=0, osc3_shape=3, osc3_level=127, osc3_routing=0, volume=40)
PLAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'play')


def sweep(level_db=LEVEL_DB):
    t = np.arange(int(SWEEP_S * RATE)) / RATE
    k = np.log(F_HI / F_LO)
    x = np.sin(2 * np.pi * F_LO * SWEEP_S / k * (np.exp(t / SWEEP_S * k) - 1))
    fade = int(0.01 * RATE)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    x = np.concatenate([np.zeros(int(0.3 * RATE)), x, np.zeros(int(0.5 * RATE))])
    return x * 10 ** (level_db / 20)


def write_wav(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(4); w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * (2 ** 31 - 1)).astype('<i4').tobytes())


def read_wav(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels()) / 2.0 ** 31


def response(x, y):
    n = 1 << int(np.ceil(np.log2(len(x) + len(y))))
    lag = int(np.argmax(np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)))
    seg = y[lag:lag + len(x)]
    if len(seg) < len(x):
        seg = np.concatenate([seg, np.zeros(len(x) - len(seg))])
    X, Y = np.fft.rfft(x), np.fft.rfft(seg)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    return f, Y / np.where(np.abs(X) > 1e-12, X, 1e-12), lag


def smooth_db(f, H, centres):
    out = []
    for c in centres:
        m = (f > c * 2 ** (-1 / 12)) & (f < c * 2 ** (1 / 12))
        out.append(10 * np.log10(np.mean(np.abs(H[m]) ** 2)))
    return np.array(out)


def run(outdir, tag, overrides, level_db=LEVEL_DB):
    os.makedirs(outdir, exist_ok=True)
    stim = os.path.join(outdir, 'sweep_%d_%+.0f.wav' % (RATE, level_db))
    x = sweep(level_db)
    if not os.path.exists(stim):
        write_wav(stim, x)
    sound = dict(EXT_SOUND); sound.update(overrides)
    p2rig.set_sound(sound)
    time.sleep(0.3)
    path = os.path.join(outdir, tag + '.wav')
    p2rig.send(p2rig.hexmsg(0x90 | (p2rig.CHANNEL - 1), NOTE, 100))
    time.sleep(0.2)
    cap = p2rig.capture(path, len(x) / RATE + 1.5, RATE)
    time.sleep(0.8)
    subprocess.run([PLAY, '--device', 'Fireface', '--channels', str(p2rig.EXT_OUT_CHANNEL), '--file', stim],
                   check=True, stdout=subprocess.DEVNULL)
    cap.communicate()
    p2rig.send(p2rig.hexmsg(0x80 | (p2rig.CHANNEL - 1), NOTE, 0))
    json.dump({'sound': sound, 'note': NOTE, 'level_db': level_db}, open(path[:-4] + '.json', 'w'), indent=1)
    y = read_wav(path)[:, 0]
    return response(x, y)


CENTRES = 1000 * 2 ** (np.arange(-17, 16) / 3)    # third octaves, 20 Hz .. 32 kHz

if __name__ == '__main__':
    outdir, tag = sys.argv[1], sys.argv[2]
    ov = {k: int(v) for k, v in (a.split('=') for a in sys.argv[3:])}
    level = ov.pop('level_db', LEVEL_DB)
    f, H, lag = run(outdir, tag, ov, level)
    db = smooth_db(f, H, CENTRES)
    np.savetxt(os.path.join(outdir, tag + '_response.csv'), np.column_stack([CENTRES, db]), delimiter=',', fmt='%.3f')
    print('%-24s lag %d  ' % (tag, lag) + ' '.join('%5.1f' % v for v in db))
