# TODO

One line per item. Measurements and reasoning go in `findings.md`, design in `design.md`.

## First
- Link HW: the Pulse 2's P.XXX does not follow (the sound and its name do, from the dump) and a cutoff turn does not reach it - both are channel messages: check the Pulse 2 MIDI Channel setting (default 1, CT's instrument is on 12) before anything else
- P006: still more noise on the plug-in - the noise level and the routed gain match the instrument (p006_noise/); LP12's stopband is ~2.5 dB high at 1-2.5 kHz at cutoff 0 and a fitted mix that fixes it breaks under drive (p2Filter notes §7): an LP12 leak that is robust to saturation
- P010: brighter on the plug-in (CT, listening)
- Filter envelope short attacks: measure with noise through the filter (p2Plugin notes §43); P004's burst
- The thump: which control leaks (oscillators and noise off, one envelope at a time) - p2Plugin notes §43
- Drive, way 1 (pragmatic, P003): a level-dependent gain on the static FUZZ fit, from the level sweep - p2Drive notes §4
- Drive, way 2 (thorough): long repeated quiet-level captures for the settling; FUZZ and TUBE as measured curves per Drive - p2Drive notes §4
- P001: 7-12 dB dark (attack and sustain), phase-fixed, hiss-matched
- P005: sustain 6-7 dB dark
- P006: 1-4 kHz 3-7 dB bright (resonance 41 / filter keytrack 95 at cutoff 0?); first 150 ms ~3 dB quiet
- P011: compare at a fixed phase - its slow LFO (sTRI) runs free on the instrument, so no take starts where the plug-in does
- P015: compare with the arpeggiator OFF on both (CT) - separates the sound from the arp, whose HOLD also latches notes from the take before; then the arp on its own, released (Arp OFF, then ON) before each take

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
- Recapture P011 with LFO 1 at a fixed phase (it runs FREE, 24 s period) to settle its sustain difference
- Drive, again: sines 50 Hz-5 kHz (and a two-tone) through EXT with the filter open, at stepped levels, for the curves' memory
- Amp Velocity: the engine moved P011 1.7 dB more than the instrument (velocity 100, Amp Velocity 95) - check the law away from velocity 64/127
- Osc 3 on DRIVE raises the baseline by about 8 drive units at any level - find why
- FB alone sings on the instrument from FB 64 (cutoff 64, ~950 Hz, -40 dB); the engine does not - frequency-dependent feedback?
- Arp Pattern (0-14): what it selects
