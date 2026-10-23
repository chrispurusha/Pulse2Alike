# Pulse2Alike - design

Living design note, started 2026-10-17.

## 1. The instrument

A monophonic analogue synth with three DCOs, noise, an external input, one filter with four modes, drive,
a VCA, two envelopes, two LFOs, an 8-slot modulation matrix and an arpeggiator. Osc 1 also has unison and
paraphonic modes.

**Sources.** This repo states only what has been measured on the instrument (captures, the rig in §5) or
seen on its panel and display. A law in the code is there because it reproduces the captures.

## 2. The oscillators

**2.1 Pitch.** The model's DCO counts a 12 MHz clock, one whole number of ticks per period.

- Pitch is held in 1/256 semitone steps. MIDI note *n* is `n·256 + 36·256`.
- The bottom octave's periods are `floor(24 MHz / f)` in two-tick units, and each octave up is one more right
  shift.
- Between semitones the **period** is interpolated linearly, not the frequency.
- **Checked against the instrument:** osc 1 at MIDI 36-96, all three shapes, measures within ±0.01 cent of this
  law, after a constant 1.5-2.7 ppm offset between the instrument's clock and the interface's (findings).
- The model's consequences, not yet measured: about 0.7 cent of error mid-semitone (audible in glides), and
  the top notes slightly sharp (MIDI 127 +1.2 cent).

Coded in `src/p2Dco.c`, checked by `tools/do-dcocheck`.

**2.2 Pulse width.** The pulse is high for `w` ticks of each period:

`w = ((W + 512)·W >> 15) · (period >> 12) >> 4`, with `W = PW << 8` (at most `0x7E00`).

That is quadratic in PW and tops out at 49 % of the period. **Checked against the instrument** across PW 16-127.
The measured duty is 0.002-0.009 of a cycle wider than the law, probably the analogue edges' slew. PW 0 is
silent.

**2.3 To measure (captures from the oscillator session, `osc/`):** amplitude against pitch, ramp curvature and
the reset, how TRI is shaped, and what SYNC, FB, X1-PWM and X3-PWM do.

## 3a. The filter (from captures, 2026-10-17)

One 4-pole resonant loop with global negative feedback. The mode picks the output.

- **Cutoff:** self-oscillation at `23.93 Hz × 2^(cutoff / 11.977)`, exponential from 0 to about 118, then
  flattening at about 23-24 kHz.
- **Resonance:** loop gain `k ≈ 0.049 × (res − 14)` (≈ 0 below 16), reaching 4 at res 96-97. That is where it
  starts to oscillate.
- **No bass compensation:** the LP passband drops by `20·log10(1 + k)`, about 14 dB at res 96.
- **Outputs:** LP24 = 4 poles; LP12 = 2 poles; BP12 = 1 + 1; HP12 = 2 poles high-pass, its passband about 15 dB
  below LP24's and unaffected by resonance. A pole-mixing multimode.
- **Not ideal:**
  - At cutoff 127 the response is not flat: a shelf, and a top roll-off from about 6 kHz.
  - The roll-off point sits below fc by an amount that grows with cutoff.
  - The resonant peak is lower at high cutoffs than an ideal loop's.
  - Each output's distortion differs (findings).
- **Next:** fit an ideal-loop model (4 one-pole stages, a feedback k, output taps and gains, plus one fixed shelf
  and one fixed top pole) to all the sweeps at once. Then add the nonlinearity from the level sweeps.

## 3b. Anomalies, and the switch for them (CT, 2026-10-17)

Every measured departure from the textbook circuit is listed here, and modelled so it can be turned off. The
plug-in gets an **Anomalies** switch: on reproduces this Pulse 2, off gives the idealised instrument. Some could
later get switches of their own. Each anomaly records its evidence, and whether it is unit-specific (drift,
tolerance) or by design.

| Anomaly | Evidence | Status |
|---|---|---|
| 1 kHz tone at −96 dBFS (+ H2) while a note sounds, entering before the VCA | findings, noise floor | to model |
| Cutoff stops following above about cutoff 118 and flattens at 23-24 kHz | self-oscillation sweep | to model |
| ±11 cent S-shaped deviation of the cutoff from exponential | self-oscillation sweep | to model |
| HP12 notch below the cutoff (about 160-190 Hz at cutoff 64, resonance 92) | HP sweeps | reproduced by the linear fit (stage 3/4 terms in the HP mix) |
| Bass shelf and top roll-off even at cutoff 127 | LP24 sweeps | in the linear fit |
| Saw ramp curvature and soft reset; triangle rounding and asymmetry | oscillator captures | to model |
| Pulse duty 0.002-0.009 wider than the law (edge slew) | PW sweep | to model |
| Filter self-oscillation distortion differs per output | mode self-oscillation | with the nonlinearity |
| Modulation reaches the cutoff as a 1 kHz staircase, each step smoothed with about a 0.3 ms time constant (off: continuous) | LFO-swept self-oscillation | to model |

## 4. Driving the instrument

Every sound parameter has a CC on the instrument's MIDI channel (OMNI at 0). Values are 7-bit and clamped to
each parameter's range.

| What | CC | Values |
|---|---|---|
| Osc 1 shape | 34 | 0 PWM, 1 SAW, 2 TRI, 3 APW, 4 UNISON-M, 5 UNISON-P, 6 UNIAPW-M, 7 UNIAPW-P, 8 PARA-8, 9 PARA-4 |
| Osc 1 PW / semitone / detune / keytrack / level | 35 / 70 / 71 / 73 / 45 | semitone 16..112 |
| Osc 2 shape | 38 | 0 PWM, 1 SAW, 2 TRI, 3 X3-PWM, 4 X1-PWM |
| Osc 2 PW / semitone / detune / keytrack / level | 39 / 36 / 37 / 40 / 46 | |
| Osc 3 shape | 44 | 0 SQR, 1 SAW, 2 TRI, **3 EXT**, 4 FB |
| Osc 3 routing | 72 | 0 MIX, 1 LEVEL2, 2 VCF, 3 DRIVE |
| Osc 3 semitone / detune / sync>osc 2 / level | 42 / 43 / 41 / 47 | |
| Noise level | 48 | |
| Cutoff / resonance | 50 / 56 | |
| Filter type | 49 | 0 LP24, 1 LP12, 2 BP12, 3 HP12 |
| Filter env amount / keytrack / velocity | 52 / 51 / 53 | bipolar, 64 = 0 |
| Drive / drive curve | 76 / 77 | 0 NONE, 1 TUBE, 2 FUZZ, 3 FX |
| Pan / volume / velocity | 59 / 57 / 58 | |
| Env F A/D/S/R, loop, trigger | 14-17, 74, 29 | |
| Env A A/D/S/R, loop, trigger | 18-21, 75, 31 | |
| LFO 1 speed / shape, LFO 2 speed / delay | 24 / 25, 26 / 27 | |
| Glide rate / mode | 5 / 62 | |
| Mod 1-4 source / amount / target | 108-119 | |
| Mod 5-8 | 90-101 | |
| Unison detune, osc 1/2 env A fade | 102, 103 / 104 | |
| Bend up / down | 105 / 106 | 0..36 semitones |

Input gain is a global setting (8 steps from −13 dB), set on the panel. With TX PARAMETER set to CC, the
instrument sends every panel edit, so a session can log where the panel is.

**Cutoff over CC is 7-bit.** For finer steps, route pitch bend
(14-bit) or keytrack to cutoff through a mod slot, calibrated against the CC steps.

## 5. Captures

**Rig (2026-10-17):**
- Fireface UC output 6 (index 5) → the Pulse 2's EXT IN.
- Pulse 2 L/R → Fireface inputs 7/8 (indices 6, 7).
- Captures go to `/Volumes/ext-ssd/Captures/Pulse2/` (the external SSD; every project's captures live there).
- MIDI over USB, port "Pulse2", **channel 12** (status `9B`/`8B`, CCs `BB`).
- Tools: G2Alike's `tools/capture` (`--device Fireface --channels 6,7`), `tools/tone`
  (`--channels 5`), `filter_response.py`, `harmonics.py`. The method follows G2Alike's
  `Docs/analogue-filter-capture-design.md`, the Voyager filter, which hit the same nonlinearity and drift
  problems.

**5.1 Oscillators.** One at a time, filter fully open, each shape at about six pitches. Wanted: wave shape,
reset spike, amplitude against pitch, and the pulse edges. The pitch is exact (§2.1), so cycles can be
averaged phase-locked.

**5.2 Filter**, through EXT (osc 3 shape EXT, osc 1/2 and noise at 0):
- Sine sweeps and multitone at several input levels, per mode, over a cutoff and resonance grid.
- Self-oscillation frequency against cutoff, which gives the cutoff law directly.
- Repeat a reference setting through each session to watch drift.
- The instrument has a "TUNE FILTER" utility that self-oscillates the filter. It is worth knowing what it
  calibrates before trusting the cutoff law across power cycles.

**5.3 Drive and VCA:** level sweeps per drive curve.

## 6. Order of work

1. A known test sound set entirely over CCs, so every capture starts from the same state.
2. Oscillator captures (§5.1); fit the wave shapes into `p2Dco.c`.
3. Cutoff law from self-oscillation, then the filter's small-signal response per mode, then its drive.
4. Envelopes and LFOs (digital: find their laws), then the mod matrix.

## 7. Presets (design 2026-10-23; built the same day except Store Sound to Slot and Restore, which write the
instrument's flash and wait for CT's go-ahead. Slots are chosen in SynthLib's bank browser, as in the siblings)

Program changes recall sounds from **one presets file**, as the instrument recalls them from its own memory,
in place of today's folder of `NNN Name.syx` files (p2Patch notes §2). Single `.syx` files stay for loading and
saving one sound.

**7.1 The file.** `presets.syx` beside `prefs.txt` in `~/Library/Application Support/Pulse2Alike/`: 500 sound
dumps back to back, each 137 bytes (p2Patch notes §1) and addressed to its own slot, so P*n* starts at byte
(*n* − 1) × 137 and the whole file is 68,500 bytes. It is a valid multi-message `.syx` by itself, which is
also what an export of it is. No file: every slot holds INIT, as an empty slot on the instrument does.

**7.2 The cache.** The file is read once into today's per-slot seqlock cache (p2Patch notes §5); a program
change reads only the cache. A store is write-through: the slot's 137 bytes are rewritten in place in the
file and the slot in the cache. Instances in one process share the cache; another process sees a store when
the file's modification time has changed, checked on the main thread when a menu opens and on Prev/Next.

**7.3 Recall.** A new instance starts on P001. Prev/Next step through P001-P500 and wrap at both ends, as the
instrument's own buttons do. A project reopened in a host keeps the sound it saved, edits and all, and shows
the preset it came from. The panel marks a sound edited since its recall or store (`P012*`).

**7.4 Reading the instrument.** The plug-in needs its own CoreMIDI input from the `Pulse2` port: a host hands
a plug-in its track's MIDI, not the instrument's replies. Each slot is requested in turn as `tools/p2dump`
does; a slot that does not answer within the timeout is empty and takes INIT (P407-P499 never answer: findings,
2026-10-17).

**7.5 Writing the instrument.** A dump addressed to a slot is a flash write (p2Hardware notes §2), so a restore
first reads each slot back (§7.4) and writes only those that differ: flash wear is spent only on real changes.
Dumps are paced so the instrument finishes each write before the next arrives. A whole restore asks first.

**7.6 Menus.** Wording follows G2Alike's "Store ... to Bank" / "Backup ... Bank" / "Restore ... Bank".

*File* - single sounds, as now: Open Patch..., Save Patch, Save Patch As..., Init Patch...

*Presets* - the presets file:
- Load Preset ▸ P001-P100 ... P401-P500 (today's Load Patch by Number, with names)
- Store Preset (back to the slot it came from)
- Store Preset to... (choose the slot; the confirmation names what it replaces)
- Revert to Stored Preset
- Export Presets to File... / Import Presets from File... (all 500; import asks first)
- Export Presets to Folder... / Import Presets from Folder... (`NNN Name.syx` files - the existing library's
  format, which is how that library comes in)

*Pulse 2* - the instrument:
- Send Sound to Pulse 2 (edit buffer, as now)
- Store Sound to Pulse 2 Slot... (one flash write)
- Backup Pulse 2 to Presets (all 500 into the presets file)
- Restore Presets to Pulse 2... (§7.5)

Reload Patch Library and the folder-walking Prev/Next (p2Draw notes §4) go.

**7.7 One instance owns the instrument.** Everything that talks to the Pulse 2 - Link (p2Plugin notes §41), Send
Sound, Store Sound to Slot, Backup and Restore - goes through whichever instance owns it, and only one does on
the machine, across hosts as well as within one. Ownership is an exclusive `flock()` on `hardware.lock` beside
`prefs.txt`: it covers other processes and other instances in the same one (each opens the file itself), and the
system releases it when the owner turns Link off, is removed, or its host quits or crashes, so it can never be
left held.
- Link on takes the lock. If another instance holds it, Link stays on but idle and the panel says the Pulse 2 is
  in use elsewhere; it takes over, and sends its sound, as soon as the lock is free (tried on the editor frame,
  as Link already runs). A reopened project with Link saved on therefore never fights another for the
  instrument, and the parameter is not changed behind the host's back.
- A one-off action (Send Sound, Store Sound to Slot, Backup, Restore) from an instance without Link takes the
  lock for its duration if it is free, and otherwise says the Pulse 2 is in use and does nothing.
- Backup and Restore hold it throughout, so Link's own sends, even from the same instance, wait until they finish.
- The MIDI input of §7.4 belongs to the owner alone, so a reply reaches only the instance that asked.

**7.8 Order of work.** The file and the cache (§7.1-7.2), Load/Store/Revert and Prev/Next, import/export, the
hardware lock (§7.7) under today's Link and Send Sound, then the MIDI input and the two hardware passes, Backup
first.
