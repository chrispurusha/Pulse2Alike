#!/usr/bin/python3
# Validates the plug-in against the instrument, patch by patch: the hardware plays its stored sound (bank select
# + program change), the plug-in renders the same .syx, and the two are compared (spectra in three windows, the
# level envelope, pitch), alongside the features the patch uses that the engine does not model yet.
# usage: patch_validate.py <patch folder> <outdir> <first> <last> [note]     P001.. as the display numbers them
import glob, os, subprocess, sys, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

HERE = os.path.dirname(os.path.abspath(__file__))
RATE = 192000
HOLD_S, TAIL_S = 2.0, 2.5
CENT = 1000 * 2 ** (np.arange(-17, 15) / 3)          # third octaves, 20 Hz .. 20 kHz
WINDOWS = (('attack', 0.0, 0.3), ('sustain', 0.5, 1.9), ('release', 2.05, 2.6))


def read(path):
    w = wave.open(path)
    x = np.frombuffer(w.readframes(w.getnframes()), '<i4').reshape(-1, w.getnchannels())[:, 0] / 2.0 ** 31
    return x, w.getframerate()


def onset(x, r):
    e = np.abs(x)
    i = np.flatnonzero(e > max(e.max() * 0.01, 1e-4))
    return i[0] if len(i) else 0


def bands(seg, r):
    if len(seg) < 256:
        return np.full(len(CENT), np.nan)
    win = np.hanning(len(seg))
    P = np.abs(np.fft.rfft(seg * win)) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / r)
    return np.array([10 * np.log10(P[(f > c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))].sum() + 1e-30) for c in CENT])


def fundamental(seg, r, guess):
    from osc_analyse import refine_f0
    return refine_f0(seg - seg.mean(), r, guess)


def harmonics(seg, r, f0, count=24):
    """Each harmonic's level (dB) and the level just beside it (the noise there), Hann-windowed."""
    seg = seg - seg.mean()
    win = np.hanning(len(seg))
    t = np.arange(len(seg)) / r
    lv, nf = [], []
    for k in range(1, count + 1):
        if k * f0 > 0.45 * r:
            lv.append(np.nan); nf.append(np.nan); continue
        at = lambda f: abs(np.sum(seg * win * np.exp(-2j * np.pi * f * t)))
        lv.append(20 * np.log10(at(k * f0) + 1e-12))
        nf.append(20 * np.log10(max(at((k + 0.5) * f0), at((k - 0.5) * f0)) + 1e-12))
    return np.array(lv), np.array(nf)


def envelope(x, r, start):
    n = r // 20
    seg = x[start:start + int((HOLD_S + TAIL_S) * r)]
    return np.array([20 * np.log10(np.sqrt(np.mean(seg[i:i + n] ** 2)) + 1e-9) for i in range(0, len(seg) - n, n)])


def features(sound):
    """The parameters a sound uses that the engine does not model yet."""
    out = []
    shape1 = sound[0]
    if 4 <= shape1 <= 7:
        out.append('osc1 %s' % ['', '', '', '', 'UNISON-M', 'UNISON-P', 'UNIAPW-M', 'UNIAPW-P'][shape1])
    if sound[6] >= 3:
        out.append('osc2 X-PWM')
    if sound[12] in (3, 4) and sound[17] > 12:
        out.append('osc3 EXT/FB')
    if sound[13] != 0 and sound[17] > 12:
        out.append('osc3 routing')
    if sound[16]:
        out.append('sync')
    if sound[36]:
        out.append('ARP')
    if sound[23] and sound[22]:
        out.append('glide')
    if sound[48] or sound[49]:
        out.append('drive')
    for m in range(8):
        src, amt = sound[54 + 3 * m], sound[55 + 3 * m]
        if src and amt != 64:
            out.append('mod%d' % (m + 1))
    if sound[28] or sound[34]:
        out.append('env loop')
    return out


def main():
    folder, outdir, first, last = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    note = int(sys.argv[5]) if len(sys.argv) > 5 else 48
    os.makedirs(outdir, exist_ok=True)
    ch = p2rig.CHANNEL - 1
    for n in range(first, last + 1):
        files = glob.glob(os.path.join(folder, '%03d *.syx' % n))
        if not files:
            print('%03d: no .syx' % n); continue
        syx = open(files[0], 'rb').read()
        # P2_FIXED_LFO=1: both LFOs' Phase at 0 (rows 81, 82), so a FREE LFO starts from a known point on both;
        # the instrument gets the changed sound in its EDIT BUFFER (7F 00), never a slot
        fixed = os.environ.get('P2_FIXED_LFO') == '1'
        if fixed:
            d = bytearray(syx[:137])
            d[5], d[6] = 0x7F, 0x00
            d[7 + 81] = d[7 + 82] = 2
            d[135] = sum(d[1:135]) & 0x7F
            syx = bytes(d)
            files = [os.path.join(outdir, 'fixedlfo_%03d.syx' % n)]
            open(files[0], 'wb').write(syx)
        sound = list(syx[7:7 + 128])
        tag = 'lfo0_' if fixed else ''
        hw = os.path.join(outdir, 'hw_%s%03d.wav' % (tag, n))
        if not os.path.exists(hw):
            if fixed:
                p2rig.send(syx.hex(), 'sleep:400')
            else:
                # the display's P001 is program 0 of bank 0; 100 sounds to a bank (findings, "program change")
                p2rig.send(p2rig.hexmsg(0xB0 | ch, 32, (n - 1) // 100), p2rig.hexmsg(0xC0 | ch, (n - 1) % 100), 'sleep:400')
            cap = p2rig.capture(hw, HOLD_S + TAIL_S + 1.2, RATE)
            time.sleep(0.8)
            p2rig.send(*p2rig.note_items(note, HOLD_S))
            cap.communicate()
        p2 = os.path.join(outdir, 'p2_%s%03d.wav' % (tag, n))
        subprocess.run([os.path.join(HERE, 'p2render'), files[0], str(note), str(HOLD_S), str(TAIL_S), p2, '96000'],
                       check=True, capture_output=True)
        xh, rh = read(hw)
        xp, rp = read(p2)
        sh, sp = onset(xh, rh), onset(xp, rp)
        line, harm = [], []
        for name, a, b in WINDOWS:
            seg = xh[sh + int(a * rh):sh + int(b * rh)]
            bh = bands(seg, rh)
            bp = bands(xp[sp + int(a * rp):sp + int(b * rp)], rp)
            # notes: the capture's own noise floor, from the silence before the note, scaled to this window's
            # length - a quiet, dark sound otherwise scores the interface's hiss as a spectral difference
            quiet = xh[max(0, sh - int(0.5 * rh)):max(0, sh - int(0.05 * rh))]
            nf = bands(np.resize(quiet, len(seg)), rh) if len(quiet) > 1000 else np.full(len(CENT), -np.inf)
            ok = (bh > bh.max() - 50) & (bh > nf + 10) & np.isfinite(bp)
            off = np.median((bp - bh)[ok]) if ok.any() else np.nan
            dev = np.sqrt(np.mean(((bp - bh) - off)[ok] ** 2)) if ok.any() else np.nan
            line.append('%s %.1f' % (name, dev))
            # notes: harmonic by harmonic - robust where a dark, quiet sound sits near hum and hiss
            hseg = xh[sh + int(a * rh):sh + int(b * rh)]
            pseg = xp[sp + int(a * rp):sp + int(b * rp)]
            if len(hseg) > rh * 0.08 and len(pseg) > rp * 0.08:
                # APW's true period is two cycles (findings, "APW"): read its harmonics on the sub-octave
                apw = sound[0] in (3, 6, 7) and sound[5] > 12
                f0 = fundamental(hseg, rh, 440.0 * 2 ** ((note + sound[2] - 64 - 69 - (12 if apw else 0)) / 12.0))
                hh, hn = harmonics(hseg, rh, f0)
                hp, _ = harmonics(pseg, rp, f0)
                ok = np.isfinite(hh) & np.isfinite(hp) & (hh > hn + 10) & (hh > np.nanmax(hh) - 50)
                if ok.sum() >= 3:
                    d = hp[ok] - hh[ok]
                    harm.append('%s %.1f (%d)' % (name, np.sqrt(np.mean((d - np.median(d)) ** 2)), ok.sum()))
        eh, ep = envelope(xh, rh, sh), envelope(xp, rp, sp)
        k = min(len(eh), len(ep))
        ok = eh[:k] > eh[:k].max() - 50
        de = (ep[:k] - eh[:k])[ok]
        name = os.path.basename(files[0])[4:-4]
        print('%03d %-15s harmonics: %-42s| bands: %-32s| env %.1f | missing: %s' % (
            n, name, ', '.join(harm), ', '.join(line), np.std(de) if len(de) else np.nan, ' '.join(features(sound)) or '-'))


if __name__ == '__main__':
    main()
