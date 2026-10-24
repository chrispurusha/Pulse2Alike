
## 3. Phase
FREE, RAND, 0, 90, 180, 270 (the instrument's own list; the manual does not describe it, and no CC reaches it).
FREE never resets the LFO; RAND starts it anywhere at each note; the others at that point of the cycle, measured:
with SAW at 0 the cutoff starts at the bottom of the ramp, and 90/180/270 move the reset a quarter, half and three
quarters of the period earlier.

## 4. Which way each shape starts
From a note at phase 0 (findings, "LFO phase and direction" and "P011"). SAW and sSAW rise from the bottom (a
positive amount raises the cutoff). The fast SINE, TRI and SQR start at the middle going DOWN (SQR low for the first
half). The slow sSIN, sTRI and sSQR start at their TOP and go down (sSQR high first). The slow ones were first read
from the self-oscillating filter, where the start of the take is uncertain; P011's pulse width settled it: with
the filter open, its sTRI on the width starts wide and narrows steadily from the first window.

## 5. The slow shapes' rate
Not a fixed fraction of the fast law: measured with sTRI on the self-oscillating filter's cutoff at speeds 4, 16,
32, 48, 64 and 96 (0.0229, 0.0763, 0.214, 0.610, 1.648, 9.98 Hz), which is 0.11 of the fast law at speed 4,
0.20 at 32 and 0.24 at 64. Interpolated between the points on a log scale and extended at the ends. The 0.197
first used held only near speed 32, where it was measured.

## 6. The bottom of the fast shapes' Speed
Below speed 16 the rate is not the 12-steps-an-octave law: measured with LFO 1's TRI on osc 1's pitch (findings
2026-10-24), periods 125 s at speed 0 (~2 minutes), 20.8 s at 4, 7.4 s at 9, 3.1 s at 14 - against 5.9, 4.6, 3.5 and
2.6 s from the law. From 5 to 16 it runs 4 steps an octave from 0.0679 Hz; from 3 to 5 it rises 0.016 Hz a step, and
from 0 to 3 0.008 Hz a step from 0.008 Hz. At 16 it meets the law (0.430 Hz). P051's slow panning sweep (speed 9)
had run twice too fast.
