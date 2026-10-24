#!/usr/bin/python3
# The engine's LEVEL2 against level2_session's takes: osc 2's envelope folded on osc 3's period (log, against osc 3 at
# 0), phase-free; shape rms and mean level per take.  usage: level2_check.py [p2render binary]
import os, sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level2_session as ls

BINS = 128


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else './p2render'
    d = os.environ.get('TMPDIR', '/tmp')

    def one(case):
        shape, s3, lv, l2 = case
        out = os.path.join(d, 'l2c_%s_%s.wav' % (os.path.basename(binary), ls.tag(shape, lv, l2)))
        ls.subprocess.run([binary, '-', str(ls.NOTE), '1.6', '0.2', out, '192000', *ls.sq.ENGINE_BASE, 'osc1level=0', 'osc2shape=1',
                           'osc2level=%d' % l2, 'osc2semitone=36', 'osc3shape=%d' % s3, 'osc3routing=1', 'osc3semitone=-48',
                           'osc3level=%d' % lv, 'osc3synctoosc2=0', 'noiselevel=0', 'cutoff=127', 'resonance=0', 'volume=40'],
                          check=True, capture_output=True)
        return case, ls.fold(out, 10.0, BINS)
    with ThreadPoolExecutor(8) as ex:
        eng = dict(ex.map(one, ls.CASES))
    errs, means = [], []
    for case in ls.CASES:
        shape, s3, lv, l2 = case
        if lv == 0:
            continue
        h = np.log(ls.fold(os.path.join(ls.OUT, 'hw_%s.wav' % ls.tag(shape, lv, l2)), 1.0, BINS) /
                   np.mean(ls.fold(os.path.join(ls.OUT, 'hw_%s.wav' % ls.tag(shape, 0, l2)), 1.0, BINS)))
        e = np.log(eng[case] / np.mean(eng[(shape, s3, 0, l2)]))
        hh, ee = np.maximum(h, -5.0), np.maximum(e, -5.0)
        ee = min((np.roll(ee, k) for k in range(BINS)), key=lambda v: np.sum((v - hh) ** 2))
        rms = np.sqrt(np.mean((ee - hh) ** 2))
        dm = 8.686 * (np.log(np.mean(np.exp(ee))) - np.log(np.mean(np.exp(hh))))
        errs.append(rms)
        means.append(dm)
        print('%-16s shape rms %.2f nepers  mean level engine-instrument %+5.1f dB' % (ls.tag(shape, lv, l2), rms, dm))
    print('all: shape rms %.2f nepers, mean level rms %.1f dB' % (np.mean(errs), np.sqrt(np.mean(np.square(means)))))


if __name__ == '__main__':
    main()
