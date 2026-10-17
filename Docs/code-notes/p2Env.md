# p2Env.c / p2Env.h - notes

One generator for both envelopes, from the amp-envelope captures (findings 2026-10-17). The filter envelope uses
the same laws until its own session says otherwise.

## 1. The tables
Measured every 8 steps plus 127: attack to −1 dB, decay/release to −40 dB, sustain in dB. Times are interpolated
on a log scale, since they grow by ratios (doubling every 8 steps through the middle). The 127 entries are
extrapolated from the curve's shape (attack: −12 dB at 34 s; release: −20 dB at 39.8 s); value 0's sustain is
silence.

## 2. Generator and VCA curve
The generator is simple: a linear attack from 0 to 1, then an exponential decay towards the sustain level
(S/127), and an exponential release towards 0. What the ear hears is the VCA's response to it, `p2_env_vca_gain()`.
That response is the measured sustain table read as a curve of the envelope's level. One curve explains three
separate measurements (findings, "one generator, one VCA curve"):
- the sustain levels;
- the amp attack's slow start (−40/−20/−6 dB at E ≈ 0.12/0.38/0.71, against 0.13/0.39/0.73 measured);
- the filter envelope decaying more slowly in log terms than the amp envelope (E's time constant 0.48 s against
  0.53 s measured at decay 64).

The times were measured at the output, so they convert to the generator through where the curve crosses
−1 dB (E = 0.955) and −40 dB (E = 0.124). The filter envelope is the same generator with no curve: it adds
2 × (amount − 64) × E cutoff steps.

## 3. Retriggering
A retrigger starts the linear attack from wherever the level is.
