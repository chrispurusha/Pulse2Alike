# TODO

One line per item. Measurements and reasoning go in `findings.md`, design in `design.md`.

## First
- P012 (CT 2026-10-23): resonance tone higher on the instrument - measured: the instrument's filter has drifted up since 10-17 (+0.6 semitone at cutoff 0 to +0.1 at 88; findings 2026-10-23), the law matches 10-17. NEXT: CT runs TUNE FILTER on the instrument, then re-measure cutoff 0/40/64/88 at note 60
- P012 (CT): left alone ~10 s, the instrument's first note sounds as if the filter glides in - what resets or drifts while idle (its slow LFO 1 drives VCF ENV AMT and RESONANCE; glide 10 on the pitch the keytrack follows)
- Sync and LEVEL2 are in (p2Plugin notes §22, §52). Left: LEVEL2 below osc 2 Level 101 1.5-4 dB loud (findings 2026-10-25, a richer form needed); the synced pulse against osc 3's square (0.78); P046, P073, P160, P228 slightly worse with it
- LEVEL2 (P006, P015): the coupled linear law is fitted (p2Plugin notes §52); CT to check by ear. Left: the engine's slew and loop saturation compress loud fast signals more than the instrument (2 kHz LEVEL2 takes, open triangle) - refit with the filter (see the Filter item)
- P010 (CT): still brighter on the plug-in; osc 1 alone, filter open, different - PARA-4 with LFO 2 on PW1 (amount 94) and PW2, so the width modulation's depth and the paraphonic voices
- P002 (CT): close; perhaps the start of the note (attack) - not certain
- P003: now gates off as the instrument's does (p2Plugin notes §55) - CT to check by ear
- P001: osc 1 and osc 3 alone, filter open, are 1.1-1.4 dB and 3.3 dB louder in the engine at every note - measure the oscillators' level laws across their range (P001 sounds much better since the pulse fixes, CT)
- Filter envelope short attacks: measure with noise through the filter (p2Plugin notes §43); P004's burst; redo `fenv_attack/` with Filter Velocity set (at 0 the envelope did not open)
- The first ~4 ms of a note over a release: the instrument's first half-cycle is smoother (P004)
- P006: 1-4 kHz 3-7 dB bright (resonance 41 / filter keytrack 95 at cutoff 0?); first 150 ms ~3 dB quiet; 2nd-4th harmonics 4/5/10 dB under over 7.5 s (how osc 2, osc 3 and the noise combine)
- Presets, still to do (design §7): Store Sound to Pulse 2 Slot and Restore Presets to Pulse 2 (flash writes - wait for CT's go-ahead); the rest is built
- The thump: which control leaks (oscillators and noise off, one envelope at a time) - p2Plugin notes §43
- Master Tune on the GLOBAL page: 420-460 Hz, as the instrument's
- Transpose on the GLOBAL page: +-24 semitones, as the instrument's
- Polyphonic mode: a full voice (filter, envelopes, VCA) per note - beyond the instrument, whose PARA-8/PARA-4 share one filter and one VCA; design first (voice count, CPU)

## Drive
- The output gate is in (p2Plugin notes §55) and the fitted quiet-input loss is off (p2Drive notes §7); P003 gates off as the instrument's does
- FUZZ at quiet Levels (14-20): the instrument still clips and lifts quiet signals (+3.8 dB against NONE at -45 dBFS in, BP12), the engine does not (0) - more gain into the clipper; refit running (`drive_shape.py 2 gated`)
- TUBE: the gated refit gained nothing (8.2 dB rms, a parameter at its bound) - its structure; a level trend of -3..-5 dB at Levels 14-24 easing to 0 by 80
- TUBE on noise (P030: noise 127 through BP12, Drive 127): 10 dB loud, same decay shape - capture noise through TUBE at a few Drives
- FUZZ at quiet EXT inputs: even harmonics ~15 dB above the instrument's (p2Drive notes §6)
- Rig: osc 3 on DRIVE raises the baseline by about 8 drive units at any level - find why
- The drive-on output gate's thresholds were measured with FUZZ; check one TUBE point

## Rig
- Build a known test sound over CCs (one osc, semitone/detune centred, filter open, envelopes flat) before every capture
- Read INPUT GAIN off the panel and record it with the EXT captures; sweep the EXT level per step

## Oscillators
- Osc 3's square against a synced osc 2 (polarity audit, findings 2026-10-24): where its edges sit relative to the sync point
- P014 3.6 -> 4.1 after APW's polarity fix (APW mixed with other sources) - check APW's own shape against its two-cycle period
- Osc 3 EXT is not built: the plug-in has no audio input - a side-chain input, as G2Alike's
- X3-PWM with sync (P053, bands 11-13 dB) and P052's attack: X1/X3 are built (p2Plugin notes §8); look at P053's filter (cutoff 28, env 127) and the sync's first-edge rule with X3
- The saw's reset: each ramp ends in a ~0.3-0.5 ms flat stretch (seen synced, findings 2026-10-24) - measure it unsynced against pitch
- Model the ramp's shape and reset spike against pitch (the pulse's duty is settled - design §2.2)
- How PWM from the mod matrix adds to the width word (the dial is dial << 8, confirmed)

## Filter
- Retake the LP12/BP12/HP12 resonance-92 and LP24 resonance-88 sweeps at −45 dBFS (LP24 confirmed compressed at −30)
- Level sweeps (−40..−6 dBFS) per mode at a few settings, for the nonlinearity
- LP12's stopband: ~2.5 dB high at 1-2.5 kHz at cutoff 0
- The modulation step shape, more closely: a faster LFO (larger steps), and the same test on pitch modulation

## Engine
- Library sweep leftovers (findings 2026-10-24): P010 ~4 dB quiet (attack/sustain/release alike); P017 PARA-8 starts ~16 dB quiet and lacks a held tail (findings 2026-10-25 'paraphonic plucks'); P051 harmonics (osc 2 synced 29 st over osc 3, LFO 2 on osc 2 pitch: the instrument's energy higher); P102 cannot be compared (unison at Detune 0 is a random draw), P052 X3 attack (9)
- Mod matrix: every target takes the modulation in its own dial steps (p2Plugin notes §51, §54); checked on cutoff, pitch, pan and the envelope rates - spot-check osc levels, volume, LFO 1 speed, PW, resonance against captures
- Capture to confirm the math sources: M-DELAY's time against amount (16 ms per step?), M-SMOOTH's rate, M-PRODUCT/MIN/MAX on two LFOs
- Capture to confirm: LFO 2's delay (a wait before it starts?)
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
