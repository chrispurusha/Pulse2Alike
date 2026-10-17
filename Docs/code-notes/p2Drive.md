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
