# TODO

One line per item. Measurements and reasoning go in `findings.md`, design in `design.md`.

## First
- tools/do-filtercheck fails "LP24 c64 r96 bass loss at 40 Hz" (-13.67 dB, wants -9.1): the target is the compressed -30 dBFS take; the -45 dBFS retake (k 4.01) gives ~-14.0 - confirm from the captures and update it
- Hiss ON once broke the engine live; OFF fixed it, ON again was fine. Not reproduced offline (3,663 renders, Hiss switched during notes, 2026-10-23); a fault guard now recovers and logs the state (p2Plugin notes §47) - if it happens again, send /tmp/pulse2alike.log (touch /tmp/pulse2alike-log first)
- Filter envelope short attacks: measure with noise through the filter (p2Plugin notes §43); P004's burst; redo `fenv_attack/` with Filter Velocity set (at 0 the envelope did not open)
- The thump: which control leaks (oscillators and noise off, one envelope at a time) - p2Plugin notes §43
- The first ~4 ms of a note over a release: the instrument's first half-cycle is smoother (P004)
- P001: 7-12 dB dark (attack and sustain), phase-fixed, hiss-matched; P001/P014 at note 48 do not brighten again after the filter envelope decays as the instrument does (~18 dB over half a second)
- P005: sustain 6-7 dB dark
- P010: brighter on the plug-in (CT, listening)
- P006: 1-4 kHz 3-7 dB bright (resonance 41 / filter keytrack 95 at cutoff 0?); first 150 ms ~3 dB quiet; 2nd-4th harmonics 4/5/10 dB under over 7.5 s (how osc 2, osc 3 and the noise combine)
- P011: compare at a fixed phase - its slow LFO (sTRI, 24 s period) runs free on the instrument, so no take starts where the plug-in does
- P013 -2 dB / P014 +2 dB in level
- P015: compare with the arpeggiator OFF on both (CT) - separates the sound from the arp; then the arp on its own, released (Arp OFF, then ON) before each take-
- Presets, still to do (design §7): Store Sound to Pulse 2 Slot and Restore Presets to Pulse 2 (flash writes - wait for CT's go-ahead); the rest is built
- Help: instructions in the Help menu (only About today) and in the release's Read Me First; update the install instructions (README has only Building)
- Master Tune on the GLOBAL page: 420-460 Hz, as the instrument's
- Transpose on the GLOBAL page: +-24 semitones, as the instrument's
- Polyphonic mode: a full voice (filter, envelopes, VCA) per note - beyond the instrument, whose PARA-8/PARA-4 share one filter and one VCA; design first (voice count, CPU)

## Drive
In order (agreed 2026-10-20; the shapes of p2Drive notes §6 are in and sound better, not perfect):
1. P003 on NONE is ~10 dB darker above 250 Hz than the instrument, so FUZZ gets a dull input (+13.5 dB at 1-4 kHz against +24.5): find what upstream - the filter near cutoff 24? Likely the same as P001/P014 not brightening at note 48 (First)
2. The quiet-input loss depends on pitch: notes 72/84 lose 2-3 dB less than note 48 (p2Drive notes §5) - fit the multi-frequency EXT captures (`192k/drive/drive_*_f{100,300,1000,3000}.wav`) for a coupling capacitor's frequency dependence, then let the meter or knee follow
3. FUZZ at quiet inputs (-30 dBFS EXT): even harmonics ~15 dB above the instrument's - a structure where the bias sets the coupling loop's operating point without lopsided clipping (e.g. the bias on the coupling path, not the clipper) - p2Drive notes §6
4. TUBE: its fitted bias sits at the fit's bound and it is 8 dB rms off on harmonics - a bias that follows the signal's level (its duty changes with Drive); a fixed bias per Drive went degenerate - p2Drive notes §6
5. Rig: the settling - long repeated quiet notes at a few Drives (FUZZ's gain climbs ~3 dB over 0.75 s; does the previous note matter?) - way 2 of p2Drive notes §4; with it, sines 50 Hz-5 kHz and a two-tone through EXT at stepped levels
6. Rig: osc 3 on DRIVE raises the baseline by about 8 drive units at any level - find why

## Rig
- Build a known test sound over CCs (one osc, semitone/detune centred, filter open, envelopes flat) before every capture
- Read INPUT GAIN off the panel and record it with the EXT captures; sweep the EXT level per step

## Oscillators
- Osc 2 X3-PWM and X1-PWM are not built: list index 3 plays APW (osc 1's shape 3) and 4 a saw - p2Plugin notes §8
- Model the pulse edges' slew (duty measures 0.002-0.009 wider than the law), the ramp's shape and reset spike against pitch
- How PWM from the mod matrix adds to the width word (the dial is dial << 8, confirmed)

## Filter
- Retake the LP12/BP12/HP12 resonance-92 and LP24 resonance-88 sweeps at −45 dBFS (LP24 confirmed compressed at −30)
- Level sweeps (−40..−6 dBFS) per mode at a few settings, for the nonlinearity
- LP12's stopband: ~2.5 dB high at 1-2.5 kHz at cutoff 0
- The modulation step shape, more closely: a faster LFO (larger steps), and the same test on pitch modulation

## Engine
- Mod matrix: per-target amount scaling (measured on the cutoff only; the other targets are provisional)
- Capture to confirm the math sources: M-DELAY's time against amount (16 ms per step?), M-SMOOTH's rate, M-PRODUCT/MIN/MAX on two LFOs
- Capture to confirm: SNG2/RET2 restart from zero, RET3's exception, FNON/FOFF glide, LFO 2's delay (a wait before it starts?)
- Osc 3's LEVEL2 / VCF / DRIVE depths and FB (depths are guesses beyond LEVEL2 at 8 Hz)
- FB alone sings on the instrument from FB 64 (cutoff 64, ~950 Hz, -40 dB); the engine does not - frequency-dependent feedback?
- Amp Velocity: the engine moved P011 1.7 dB more than the instrument (velocity 100, Amp Velocity 95) - check the law away from velocity 64/127
- Arp Pattern (0-14): what it selects
- Arp SOFT and HARD: measure their velocity offsets (the plug-in uses -32 and +64)
- Arp, by program change: does a chord kept by one HOLD sound start again after a non-arp sound, in the next HOLD sound? (the plug-in does so with Anomalies on - p2Plugin notes §45)
- The 1 kHz leak (−96 dBFS with a note sounding): decide whether to model it

## Plug-in
- Link: send the program change on all 16 channels, so the P number follows whatever the Channel setting (only the Pulse 2 listens on its USB port) - offered to CT 2026-10-20, undecided
- Value text in real units (times, rates, semitones) where the laws are measured; the panel shows raw values now, as the instrument does
- SynthLib: maximise the C and reduce the C++ (CT 2026-10-21) - port src/fileBrowser.cpp, bankBrowser.cpp and prefs.cpp to C; the VST3 wrapper and views stay C++/Obj-C++ as the SDK requires

## DO NOT RE-TRY
- Four one-pole stages with LP24 at the end (per-stage poles): worse than the free-mix fit, implausible stage ratios, no HP notch (findings, first linear filter fit)
- Fitting an engine constant to one take of a patch with detuned oscillators: their slow beat moves a band by up to 10 dB take to take (P006's LEVEL2 depth of 3, reverted)
- Drive structures already rejected against the level sweep - p2Drive notes §4
