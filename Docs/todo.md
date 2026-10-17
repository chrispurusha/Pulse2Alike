# TODO

One line per item. Measurements and reasoning go in `findings.md`, design in `design.md`.

## Rig
- Build a known test sound over CCs (one osc, semitone/detune centred, filter open, envelopes flat) before every capture
- Read INPUT GAIN off the panel and record it with the EXT captures; sweep the EXT level per step

## Oscillators
- Fit OSC_INTO_FILTER and the loop saturation to the saw-level table (findings: level 127/64/32 harmonics)
- Level law into the engine: ((CC − 12.6)/114.4)^0.864, silent below 13; detune = 2/256 semitone per step (both measured)
- Capture each shape at six pitches, filter open (design §5.1)
- Find how PWM (mod matrix, LFO) adds to the width word; the dial is dial << 8 (confirmed)
- Model the pulse edges' slew (duty measures 0.002-0.009 wider than the law)
- Model the ramp shape, reset spike and amplitude against pitch from the captures
- Osc 3, sync, FB, X1/X3-PWM, APW, unison and paraphonic modes

## Filter
- Modulation into the cutoff at 1 kHz with a ~0.3 ms smoother when Anomalies is on, continuous when off (measured: findings 2026-10-17); then run mod_step's analysis on the plug-in's output to compare
- Measure the step shape more closely: a faster LFO (larger steps), and the same test on pitch modulation
- Retake the LP12/BP12/HP12 resonance-92 sweeps at −45 dBFS (LP24 confirmed compressed at −30)
- Fit two 2-pole sections (each with its own damping) inside the global loop; the one-pole cascade fails (findings)
- Retake LP24 resonance 88 at −45 dBFS
- Level sweeps (−40..−6 dBFS) per mode at a few settings, for the nonlinearity
- Keytrack law (CC51) against note
- Filter envelope amount law (CC52)

## Engine
- Capture to confirm the math sources: M-DELAY's time against amount (16 ms per step?), M-SMOOTH's rate, M-PRODUCT/MIN/MAX on two LFOs
- Capture to confirm: SNG2/RET2 restart from zero, RET3's exception, FNON/FOFF glide, LFO 2's delay (a wait before it starts?)
- LFOs + mod matrix (13 of P000-P014 use mod slots): measure rate law, shapes, delay, phase, per-target amount scaling
- APW (osc 1 shape 3): P006/P010/P013 miss by up to 46 dB
- Looping envelopes, osc 3 routing, sync, drive; rerun tools/patch_validate.py 0 14 after each
- The 1 kHz leak (−96 dBFS with a note sounding): decide whether to model it
- Envelopes, LFOs, mod matrix, glide
- Drive curves and VCA
- Velocity, pitch bend, mod wheel

## Plug-in
- Import the instrument's sound dumps (.syx, saved by SynthEdit's Pulse 2 layout) as presets, to A/B patches against the instrument
- Connect the remaining pages' parameters as each part is built (most are shown and saved only)
- The value-text formats per parameter (times, rates, semitones), once their laws are measured
- Oversampling selectable (1×/2×/4×, economy) for CPU (CT 2026-10-17); fixed at 4× now
- Press/drag/release in SynthLib's tSynthLibPanel, replacing p2Draw's click-gap guess
- Amp envelope into the engine from the measured laws (findings: decay/release exponential, attack (t/T)^2.5, the time tables, sustain curve)
- Filter-envelope session: the same captures through the cutoff (self-oscillation tracks it), plus loop and trigger modes
- Velocity
- Keyboard tracking of the cutoff
- An Anomalies on/off parameter switching every entry of design §3b
- An editor panel

## DO NOT RE-TRY
- Drive: TUBE's H3 and FUZZ's even harmonics (needs captures at other frequencies: the curve has memory)
- Measure osc 3's LEVEL2 / VCF / DRIVE depths and FB
- Rotary dial drag (the siblings have it): SynthLib panel view must report uncaptured drag positions; then Controls > Rotary
