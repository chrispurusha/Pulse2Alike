# p2Filter.c / p2Filter.h - notes

The filter as measured (design §3a, findings 2026-10-17): one resonant 4-pole loop, the mode choosing a mix of
its signals. Checked offline by `tools/do-filtercheck`.

## 1. The cutoff law
The pole frequency is the measured self-oscillation frequency, `23.93 Hz × 2^(cutoff / 11.977)`. Above about
23.6 kHz it bends over smoothly (the ceiling seen above cutoff 118). In an ideal loop the self-oscillation
frequency equals the pole frequency, so the plug-in rings exactly where the instrument does. The small-signal fit
preferred poles 5.6 % higher (`beta` = 1.056). That disagreement is open: the fit trades it against its free
output mixes.

## 2. The feedback
k against resonance, from the measured bass loss (`20·log10(1 + k)`). The bass loss is linear, so these are
the reliable numbers, unlike the peak heights, which compress. k reaches 4 at resonance 97, where the
instrument starts to oscillate, then rises 0.03 per step (provisional: it sets how hard the oscillation drives
the saturation).

## 3. The output mixes, shelf and top poles
From the free-mix linear fit (`tools/filter_fit.py`, 0.46 dB rms over every sweep): each mode is a weighted sum
of the input, the loop input and the four stage outputs. The shelf (+2.9 dB below about 200 Hz) and the 5.7 kHz
and 42.5 kHz poles sit outside the loop.

## 4. The saturation
`tanh(3.1·u)/3.1` at the loop input. The scale is chosen so a sine of amplitude 0.1 (−20 dBFS at EXT IN, in the
plug-in's units) gives a third harmonic near the measured −41 dB. Provisional: one saturation point, where the
instrument's distortion differs per output (findings). The level series will refine it.

## 5. The loop solve
Zero-delay: the TPT one-poles let stage 4's output be written as `G^4·u + S`, with S from the stage states.
So the loop input is solved exactly (`u = (x − k·S) / (1 + k·G^4)`) before the saturation, with no one-sample
delay in the feedback to detune the resonance.

## 6. The stopband
The first fit of the output mix (sweeps at -45 dBFS) could not see far below the cutoff, and left small weights on
the input and the first stage. They set a floor: far above a low cutoff the response stopped falling (LP24 about
48 dB down), where the instrument's goes on past 100 dB. A saw through LP12 and LP24 at cutoffs 0-127
(`tools/filter_mix_fit.py`, `lowcut/`) refitted just those weights; the later stages', which carry the resonant
shape, are as before. Weighted error over all the harmonics: LP12 3.5 -> 2.1 dB. LP24 5.1 -> 3.7. Removing LP24's leak outright
made P001/P013/P014 10-17 dB darker than the instrument: it does leak, only less than the first fit said. LP12's level low
down fell 0.9 dB, which it had been loud by. This was the plug-in's sustain being brighter than the instrument's at
low notes in P004/P007/P008/P009/P012 (CT).
