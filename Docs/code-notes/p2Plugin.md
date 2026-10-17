# p2Plugin.c - notes

## 1. The parameters
Ranges follow the instrument's, 0..127 dials where it has them, so a captured setting can be typed in. The
ids are saved by projects: append, never insert.

## 2. Width from the dial
The dial value shifted into the width word's top byte, confirmed against the instrument across PW 16-127
(findings 2026-10-17).

## 3. Note priority
Last note, with a stack so releasing the top note returns to the one held under it. The instrument's own
priority and retrigger behaviour (GLIDE MODE, ENVF/ENVA TRIGGER) are not yet modelled.

## 4. Oscillators into the filter
The DCO mix (±1 at full level) is scaled by 0.3 before the filter, which sets how hard the oscillators drive
its saturation. Provisional, until the level captures (osc levels 127/64/32) say how hard the instrument's
oscillators drive it.

## 5. Oversampling
The voice (oscillators and filter) runs at 4× the host rate, and comes down through a 64-tap Blackman-windowed
sinc that cuts at 0.45 of the host rate. Fixed for now; selectable later for CPU (todo).

## 6. The gate is the VCA
The oscillators and the filter run whether or not a note is held, as on the instrument. The gate multiplies
the filter's output, so a self-oscillating filter is silent until a note opens it.

## 7. Cutoff and resonance glide
Both are continuous parameters, not 127 steps, and the filter follows them through a 3 ms one-pole glide
updated once per host sample. Stepping a whole semitone per CC value, applied instantly, zippered audibly (CT,
2026-10-17). The instrument itself moves its cutoff smoothly between MIDI steps, so a glide is the faithful
choice as well as the clean one.

## 8. Shapes not built yet
The shape lists are the instrument's (10 for osc 1, 5 for osc 2), but the DCO plays only PWM, SAW and TRI so
far, plus APW. Any other entry plays a saw until its mode is built (unison, X1/X3-PWM); PARA-8/4 are voices (§12).

## 9. Pitch offsets and levels, as measured
Semitone and detune are offsets to the pitch before the period law, detune 2/256 of a semitone per step, which
is why it inherits the law's mid-semitone error exactly as the captures show. The level law,
`((CC − 12.6) / 114.4)^0.864` and silent below that, was read at the output, so it may still hold some of the
filter's compression (findings). Osc 3's SQR is the DCO's pulse at its widest width, pending a capture.
Noise is white (xorshift), through the same level law, also pending a capture.

## 10. The control tick
Envelopes and the cutoff target are worked out on a control tick: every 1 ms with Anomalies on, which is the
instrument's measured update rate, and every host sample with it off. The VCA and the cutoff then follow their
targets through a one-pole with a 0.3 ms time constant, the measured smoothing of each step (findings,
"cutoff modulation"). So with Anomalies on, modulation reaches the filter as the instrument's softened 1 kHz
staircase. The cutoff target is the knob (after its 3 ms glide), plus the filter envelope × amount, plus
keytrack × (note − 60). The amount's range (±127 steps at full) and the keytrack reference note are
provisional, pending the filter-envelope session.

## 11. Triggering
SNG1 and SNG2 trigger the envelope only on a fresh note (no other key held), and are legato otherwise. RET1,
RET2 and RET3 trigger on every note. SNG2 and RET2 restart the attack from zero; the others start it from
wherever the envelope is. The SNG/RET split is measured (findings, "triggers"). The from-zero variants and
RET3's exception are not yet confirmed by capture, so RET3 is treated as RET1 for now (todo).

## 12. Paraphonic voices
PARA-8 and PARA-4 (osc 1 shapes 8 and 9) run 8 or 4 voices into the one filter, VCA and pair of envelopes, as
measured (findings, "paraphonic modes"). A PARA-8 voice is one pulse at osc 1's pitch offsets and width. A PARA-4
voice adds a second pulse at osc 2's, scaled by osc 2's level relative to osc 1's. A held note again reuses its
voice. A new note takes a free voice, else steals the most recent, which is what the captures show. Voices fade
in and out over a provisional 20 ms, until OSC1/OSC2 ENVA FADE is measured. The envelopes keep the mono trigger
rules (the first note from silence, or every note in RET modes).

## 13. The mod matrix
Eight slots, each source × (amount − 64)·|amount − 64| / 32, summed per target on the control tick, in the
target's own units. Measured on three targets, all the same law: cutoff (steps), pitch (semitones) and osc
level (dial steps, then the level law; findings, "mod matrix scaling"). The same law is used for the other
targets (PW, resonance, volume, LFO speed, env amount) until they are measured. Sources built: LFO 1, LFO 2, LFO 2 × amp env, both envelopes, velocity,
keytrack and pitch follow ((note − 64)/64). The controller sources (mod wheel, pressure, bend, breath, CTRL X)
and the math sources read 0 until they are wired.

## 14. LFO 2
LFO 2 has no shape setting; it is taken as a triangle. Its delay is a fade-in from the first note, over the
attack time law (provisional, unmeasured).

## 15. Volume, velocity and the VCA
Measured (findings, "velocity and volume"): the level is one curve of envelope × effective volume, where
effective volume = volume + velocity × (amp velocity − 64)/64. The volume law is that curve. It also predicts
the sustain table (measured at volume 40) to about 1 dB, which is why one curve serves both. Filter velocity
adds (value − 64) × velocity / 128 cutoff steps.

## 16. Loading a patch
`p2_load_patch()` reads the `.syx` (`p2Patch.c`) over the current values and hands every parameter to the host
through `synthlib_plugin_param_edited()`, so the host sees the change (automation, undo) and the processor
receives it the normal way. The plug-in's own settings (oversampling, Anomalies) are left alone.

## 17. Glide
Measured (findings, "glide"): every millisecond the pitch moves towards the note by x = distance × k(rate) / 2^17
(1/256-semitone units), rounded as floor(x) + ceil(x), so a glide never stalls short of the note. It moves at
least one unit a millisecond (3.9 semitones a second), which is all the slow rates ever do over an octave.
k(rate) × 2^17 = 2^(17.129 − 0.12697 × (rate + 10)) up to rate 74, then 265.16 − 2.0916 × (rate + 10). Against
the captured glides (48 → 60 at rates 48-112) this law is within 0.01-0.06 semitone rms. OFF jumps, NORM always
glides, and FNGR glides only on a legato note. FNON and FOFF are taken as FNGR until what separates them is
measured.

## 18. The math destinations and sources
M-ACCU, M-PRODUCT, M-DELAY, M-SMOOTH, M-MIN and M-MAX are mod targets (25-30) whose results are sources (17-22).
The slots run in order, so a slot sees what earlier slots fed in this tick.
- **M-ACCU, M-PRODUCT, M-MIN, M-MAX:** the sum, product, lowest and highest of their inputs, where an input is
  source × (amount − 64)·|amount − 64| / 4096, clipped to ±1.
- **M-DELAY:** a slot writes its source, inverted for amounts below 64, |amount − 64| × 16 ms ahead into a
  1024 ms line; the output is what arrives now.
- **M-SMOOTH:** a lag on the slot's source, moving (k + k²/256)/2048 of the way per millisecond, k = |amount − 64|.

K-HIGHEST and K-LOWEST are the highest and lowest held keys, (note − 64)/64. MOD1 AMOUNT shifts slot 1's amount.
These follow the instrument's behaviour as far as studied. M-DELAY's timing and M-SMOOTH's rates are to be
confirmed by capture (todo).

## 19. Output gain and Master
The final gain is 3.926: the instrument's own level, as captured through the rig (Fireface inputs at +4 dBu, the
same path the instrument is heard through). The same saw at Volume 40 measured −14.1 dBFS on the instrument and
−22.0 from the engine at the previous 1.58 (which was itself +10 dB on the first version's 0.5), so +7.9 dB. Master Volume (default 127) is the plug-in's own
volume after everything else, with a squared taper (−12 dB at 64, −6 dB at 90). The sound's Volume stays as the
instrument's.

## 20. Program change
Bank select (CC 32) and program change pick a sound as the instrument does, as measured: P(100 × (bank mod 5) +
min(program, 99) + 1). Bank 1 program 0 is P101, programs 99 and 100 are both P100, and bank 2 program 5 is P206.
Every `.syx` in `iCloud Drive/Patches/Pulse2` is read once when the plug-in starts (`p2_patch_cache_load`, about
68 KB). A program change only copies a cached sound, on the audio thread with no file access, then tells the
host of each parameter it changed. Program and Bank are hidden and never saved, so reopening a project restores
its sound as edited rather than reloading the program.

## 21. Unison
Measured (findings, "unison"): UNISON and UNIAPW are eight pulse (or APW) oscillators at osc 1's width, spread
symmetrically about the note, Unison Detune × 1.25 / 256 semitone apart (15.6 cents at 32, 31.1 at 64, 62 at
127). M is monophonic: the newest note, with glide. P shares the eight between the held notes, which so far is
provisional: they are split evenly, and the captured chord was more lopsided than that. Each oscillator is scaled
so the eight come out near the measured level, about 5.5 dB below one pulse at full level. Osc 2 and osc 3 play
as usual alongside.

## 22. Sync
OSC3 SYNC>OSC2 makes osc 3 the master of osc 2: osc 3's main edge restarts osc 2, which holds at the end of each
cycle until then (p2Dco notes §8). Osc 3 runs whether or not its level is up, as on the instrument, where sync
works with osc 3 silent.

## 23. Saving
A save writes the parameters through p2_patch_to_syx, keeping the unmodelled bytes of the dump the sound came
from (a file, or the library's copy after a program change). Saving into the library folder under a number
updates that program at once. Init sets every sound parameter to its default and forgets the dump.

## 24. Name, file and the plug-in's own state
The sound's name and its file belong to the instance: the panel shows this instance's, every sync. Both go in
the plug-in's own block of the saved state ("P2S1": name, the kept dump, path), so a reopened project shows its
name and file, and saves as before. A rename changes only the name; it reaches a file at the next save.

## 25. Osc 3's routing and FB
As the manual describes them: MIX into the mixer; LEVEL2 adds osc 3 to osc 2's level; VCF adds it to the cutoff
(audio-rate filter FM, the filter recomputed every oversampled sample); DRIVE adds it to the drive amount. Only MIX
puts osc 3 in the mixer. On the three control routings osc 3 is AC coupled (a high-pass near 14 Hz), measured with
osc 3 as an 8 Hz square on the self-oscillating filter: each edge kicks the cutoff and it decays back in about
30 ms. The kick is 28 cutoff steps per unit of osc 3 (+-1) at full level, scaled by the oscillator level curve
(about 12 steps at level 32, 56 at 127 across a square's full swing). LEVEL2 measured: osc 2's level plus osc 3's
level x osc 3, floored at zero (8 dB between the states at level 32, as that predicts; silent in one state from 64).
DRIVE: 30 drive units per unit of osc 3 at full level, measured (findings, "osc 3 to DRIVE"). FB, osc 3's fifth
shape, SUBTRACTS the drive's output from the mixer (negative feedback, findings "FB"), at 5.7 × osc 3's level:
with a saw that matches the instrument's level within 1.4 dB at every FB. The instrument also sings with FB alone
(from FB 64 at cutoff 64, near 950 Hz, quietly), which one gain cannot do: its feedback must be stronger near the
filter's corner than in the passband. Not reproduced yet. A tiny noise seed lets a loop start, as the
instrument's noise floor does.
## 26. The paraphonic voice fade
Measured (findings, "voice fade"): in PARA-8/PARA-4 a released voice dies away while the others hold the amp
envelope open, as a release stage of R − 5.5 − 0.61 × (127 − Fade), R the amp envelope's Release: from two points
(Fade 127 and 100 at R 70) and checked by the rest (Fade 83 almost at once, 64 and below at once, R 40 at once
whatever Fade). Osc 2's part of a PARA-4 voice uses osc 2's Fade. The fade in is not changed by Fade.

## 27. LFO phase at a note
What restarts an LFO is the FILTER envelope's trigger, following that envelope's Trigger mode (SNG on a fresh note
only, RET on every note). When it triggers, LFO 2 restarts at its Phase setting and its delay starts again, and
LFO 1 does too if its shape is one of the fast five. The slow shapes (sSIN on) are never restarted by a note: they
run free whatever their Phase, which is why two identical takes of P011 (sTRI) started at different points.
## 28. Performance controls
Pitch bend, the mod wheel, pressure (channel aftertouch), breath (CC 2) and the sustain pedal (CC 64) are hidden
parameters mapped to their MIDI controls, which is how a VST3 host delivers them (the AU passes the same MIDI to
the same parameters); they are played, never saved, and a program change or Init leaves them alone. Bend moves
every oscillator by Bend Up or Bend Down semitones at full throw, and is also the PITCHBEND mod source (-1..+1).
The wheel, pressure and breath are mod sources 0..1, and LFO1*MODW / LFO1*PRS are LFO 1 times the wheel or
pressure. V.RELEASE is the last note-off's velocity. The pedal holds released notes until it is lifted (64 and
up is down). CC 7 is the sound's Volume, as on the instrument. CONTROL-X (a global choosing a CC) is not wired.
Depths are as the mod matrix's own; none of this is measured against the instrument yet.

## 29. Filter velocity scales the envelope
Velocity's term, (Filter Velocity − 64) × velocity / 128 steps, is added to the envelope amount's and the sum is
multiplied by the filter envelope: velocity makes the envelope deeper or shallower, as the manual's "the overall
modulation ... is the sum of both the ENV F Amount and Filter Velocity" says. With the envelope at full (the
earlier velocity captures, sustain 127) it reads as a plain offset, which is how it was first modelled. P011 showed
the difference: its envelope sustains at 47, where velocity adds about 9 steps, not 25 (findings, "P011").

## 30. The pulse's level
On the instrument a pulse is quieter than the saw against which the plug-in's output was set: with the filter
open, PWM (width 64) measured 4.4 dB and APW 4.2 dB (every width) below what the engine made, while the saw and
triangle agree. Every pulse in the mix (osc 1's PWM and APW, the unison and paraphonic voices, osc 2's PWM, osc 3's
SQR on MIX) is scaled by 0.61. Only in the mix: osc 3's square as a control (LEVEL2, VCF, DRIVE) keeps its full
size, which is what those depths were measured with.
