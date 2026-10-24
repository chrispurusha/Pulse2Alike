#!/usr/bin/python3
# Compares two patch_validate.py outputs (a baseline and a candidate), patch by patch: the mean of the harmonic,
# band and envelope scores, and which got worse by more than 0.5 dB.  usage: patch_regress.py base.txt candidate.txt
import re, sys


def scores(path):
    out = {}
    for line in open(path):
        m = re.match(r'(\d{3}) ', line)
        if not m:
            continue
        harm = [float(x) for x in re.findall(r'(?:attack|sustain|release) ([\d.]+) \(\d+\)', line)]
        bands = [float(x) for x in re.findall(r'(?:attack|sustain|release) ([\d.]+)(?:,|\|)', line.split('bands:')[1])]
        env = float(re.search(r'env ([\d.]+)', line).group(1))
        out[m.group(1)] = (harm, bands, env)
    return out


a, b = scores(sys.argv[1]), scores(sys.argv[2])
total = [0.0, 0.0]
for n in sorted(a):
    ha, ba, ea = a[n]
    hb, bb, eb = b[n]
    mean = lambda h, bd, e: (sum(h) + sum(bd) + e) / max(1, len(h) + len(bd) + 1)
    ma, mb = mean(ha, ba, ea), mean(hb, bb, eb)
    total[0] += ma
    total[1] += mb
    flag = '  WORSE' if mb > ma + 0.5 else ('  better' if mb < ma - 0.5 else '')
    print('%s  %5.2f -> %5.2f  (harm %s -> %s | bands %s -> %s | env %.1f -> %.1f)%s' % (
        n, ma, mb, '/'.join('%.1f' % x for x in ha), '/'.join('%.1f' % x for x in hb),
        '/'.join('%.1f' % x for x in ba), '/'.join('%.1f' % x for x in bb), ea, eb, flag))
print('total %.2f -> %.2f' % tuple(total))
