# p2Dco.c / p2Dco.h - notes

## 1. The pitch origin
Pitch 0 is MIDI note −36, so a MIDI note is `n·256 + 36·256`. The range is 196 semitones (`0..0xC400`).

## 2. The base periods
The period of each semitone of the bottom octave, in two-tick units, is `floor(24 MHz / f)`, with `f` the
equal-tempered frequency of MIDI note `i − 36`. `tools/dcocheck` checks the law against the frequencies captured
from the instrument (design §2.1).

## 3. The period law
`(base − slope·frac/256) >> (octave + 1)`. The period, not the frequency, is interpolated between semitones,
which is design §2.1's 0.7 cent. Integer arithmetic throughout, so the reproduction lands
on the same whole-tick periods.

## 4. The pulse width
design §2.2. The result is in ticks before the main edge.

## 5. polyBLEP
Two-sample polynomial band-limited step, the usual one. A stand-in until the captures say what the edges look
like. The real edges are analogue and slower than a step.

## 6. The wave shapes
Provisional: an ideal saw, triangle and pulse. The phase resets at the main edge, and the pulse is high for
its last `pulseFraction` of the cycle. Polarity and shape come from captures (design §5.1).

## 7. APW
Measured (findings, "APW"): the pulse width alternates between w and 1 − w on successive cycles, so the true
period is two cycles, with a sub-octave that vanishes at PW 127 where both widths are about a half. The DCO
counts its main edges and takes the complement on odd cycles. The edge corrections follow the width in use.

## 8. Sync
Measured (findings, "sync"): with OSC3 SYNC>OSC2, osc 3 is the master, and every one of its cycles starts osc 2
afresh. Osc 2 runs one cycle and then holds at the end of it until the next restart. So a slave tuned above
the master plays its ramp and then a flat stretch, the shape of a timer that the master's edge restarts and that
stops when its own period runs out. A slave tuned below the master is cut short by the next restart.
