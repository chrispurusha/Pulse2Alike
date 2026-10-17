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
