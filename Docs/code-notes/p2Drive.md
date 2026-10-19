# p2Drive.c - notes

The drive is analogue, at the VCA after the filter ("Amplifier with saturation", the end of the chain). The
curve picks one of the instrument's circuits; Drive sets how hard it is driven. NONE passes the signal untouched,
and Drive then does nothing (measured: identical output at every Drive).

## 1. The curves
Each is: gain set by Drive, then a clipper with its own positive and negative ceilings, with a bias and a coupling
capacitor charged by its own output (which moves the clipping point as it is driven, the slope seen on the
captured flats), then a one-pole shelf. TUBE is lopsided (the manual's "asymmetrical", strong 2nd harmonic),
FUZZ symmetric and close to a square. Fitted cycle by cycle to 1 kHz sines through EXT at three levels and five
Drive settings (`tools/drive_fit.py`), within about 13% (TUBE) and 11% (FUZZ) of the peak. Checked against a saw
it was not fitted to: levels relative to NONE within 0.4-2.6 dB, FUZZ's odd harmonics within 2 dB; TUBE's 3rd
harmonic about 15 dB weak and FUZZ's even ones about 10 dB weak. **Approximate.**

## 2. Units
The curves were measured as the instrument's output at Volume 40. The engine's signal before the VCA maps onto
that by 0.888: the engine at Volume 40 is 7.9 dB below the instrument (the same saw: −22.0 against −14.1 dBFS),
times the VCA at 40 and the plug-in's output gain.

## 3. FX
Not in the manual: it selects the return of an effects board planned for the instrument and never made. With no
board, nothing comes back, and the instrument is silent (measured, with the external input and with the
oscillators, at every Drive). Anomalies on: silent, as the instrument. Off: as NONE.

The 0.888 is in the instrument's units and does not depend on the plug-in's output gain: when that gain rose to
match the instrument (p2Plugin notes §19), the engine's level before the VCA was unchanged.

## 3. FUZZ, refitted to the instrument's own oscillator (2026-10-19)
A triangle from osc 1 through the open LP24, captured with Drive Curve NONE (the input) and FUZZ at Drive 0, 16,
32, 64, 96 and 127, at osc levels 127 and 64 (`/Volumes/ext-ssd/Captures/Pulse2/drive_tri/`). The same structure as
§1, fitted cycle by cycle with the NONE take as the input in output units: 7% of the peak against 23% for the 1 kHz
EXT IN fit, which it replaces. Drive 16 is now a table point (P003 sits at 17).
Open, both seen in the same captures:
- below about -35 dB of input the instrument's FUZZ falls away faster than its input (osc level 16: -6 dB at Drive 0,
  where level 24 gains 2 dB) - an expansion this structure cannot make. The engine is 6-14 dB loud there, and P003's
  sustain (filter closed to 24) is there: P003 is 6-9 dB loud and 20 dB dark. Two expander forms (after the gain, on
  the raw input) did not fit; the shapes say the small-signal path is rounded, not gated.
- TUBE fits neither this structure nor an input-coupled one: its positive part narrows as Drive rises, a bias that
  moves with Drive, which the feedback coupling here cancels. TUBE keeps its 1 kHz fit.
