# Findings

The history: measurements, completed work, and the traps that cost time. Newest last.

## 2026-10-17 - project started

- Rig cabled by CT: Fireface out 6 (index 5) → EXT IN; Pulse 2 L/R → Fireface inputs 7/8 (indices 6/7); USB-MIDI port "Pulse2".
- First note test: note 60 velocity 100 sent on channel 1, then on all 16 channels, while capturing
  inputs 6,7 at 96 kHz. Both channels stayed at −104 dBFS rms (the floor). The MIDI port accepted the
  messages. Not yet known whether the instrument received them or the sound was silent.
- The DCO law (design §2.1) is in `src/p2Dco.c`; A4 = 440.012 Hz. `auval -v aumu P2al CPur` passes.
- **The instrument is on MIDI channel 12** (CT). Note 60 on channel 12 (`9B 3C 64`) sounds: about −19 dBFS rms on
  both outputs with the current sound, released to the floor by about 1.5 s after note off. Why the earlier
  all-16-channels test was silent is not known (the channel may have been set since).
- That capture's fundamental is 130.777 Hz, an octave below note 60 (130.813 Hz) and 0.5 cent flat. The sound's
  semitone and detune settings weren't read, so this says nothing yet about the pitch law. Repeat with a known
  sound (semitone 64, detune 64, one oscillator).

## 2026-10-17 - first oscillator and filter captures

All at 96 kHz (Live was holding the Fireface), Pulse 2 volume CC57 = 40. **Volume 100 clips the Fireface
inputs** (peaks at full scale, −3 dBFS rms): the first saw take was useless. The test sound is `p2rig.TEST_SOUND`.
Takes are in `/Volumes/ext-ssd/Captures/Pulse2/`.

**Pitch law confirmed.** Osc 1 saw at MIDI 36/48/60/72/84/96 measures within ±0.01 cent of design §2.1 at every
note, after a constant +2.0 to +2.7 ppm offset between the instrument's and the interface's clocks
(`osc_analyse.py`).

**Saw shape (osc 1, cutoff 127).**
- It is a **falling ramp with an upward reset**.
- The ramp is curved. Its bow shrinks as the note rises, and a rounded hump follows each reset.
- Harmonics 4-12 sit about 3 dB below an ideal saw (1/k) at notes 36-60. That is the waveform itself:
  cutoff 110 and 127 give the same spectrum at note 48.
- At note 96 the top harmonics fall away. That is the filter at cutoff 127, which is not fully open (below).

**Filter keytrack:** CC51 = 64 is zero tracking. Value 0 is −100 %: at note 96 it pulled the output down by
about 32 dB. At cutoff 127 the cutoff is clamped, so positive tracking above the reference changes nothing.

**EXT IN works.** Osc 3 shape EXT (CC44 = 3), level 127, routing MIX. With a 1 kHz sine from Fireface output 6
and the cutoff at 127:

| Input (dBFS) | Gain | H2 | H3 |
|---|---|---|---|
| −30 | +1.6 dB | −49 dB | −62 dB |
| −20 | +1.5 dB | −40 dB | −41 dB |
| −10 | +0.0 dB | −33 dB | −19 dB |

So the path saturates symmetrically (H3) from about −20 dBFS in. Small-signal work stays at −30 dBFS. INPUT
GAIN (a global) was not read.

**LP24 response, resonance 0** (`filter_sweep.py`: a −30 dBFS log sweep, 20 Hz-40 kHz, note 60, third-octave
smoothed; `filter/lp24_c*_response.csv`):
- Low-frequency gain is about +4.5 to +5 dB. Even at cutoff 127 there is a gentle shelf down from about 100 Hz
  (+4.5 dB) to 1 kHz (+1.7 dB): **fully open is not flat**, just as on the Voyager. The top is −3 dB at
  6.3 kHz and −31 dB at 32 kHz.
- **The cutoff moves about one semitone per CC step.** At the −25 dB point: cutoff 40 → 500 Hz, 60 → 1.6 kHz,
  80 → 5 kHz, 100 → 12.7 kHz. That is 1.68, 1.64 and 1.34 octaves per 20 steps, flattening near the top.
- The slope reaches about 17 dB per octave within the measured range. The floor is about −50 dB below the
  response (noise and leakage).

## 2026-10-17 - at 192 kHz (CT set the Fireface; Live was not holding it)

**Noise floor.** With no note, −85 dBFS rms (−136 to −113 dBFS per third octave, rising with frequency). With a
note held and EXT silent, −78 dBFS rms (−110 to −90 dBFS per third octave), **plus a 1 kHz tone at −96 dBFS and
its 2nd harmonic** that are present only while the note sounds. No player was running, so the tone enters before
the VCA; a digital leak of some kind. It is harmless for −30 dBFS sweeps but is part
of the instrument's sound.
- **The sweep method's floor** (sweep playing, osc 3 level 0): −66 to −71 dB below 1 kHz, about −46 to −50 dB above.
  Every filter fit masks bands within 10 dB of it (`filter/floor_ext0_response.csv`).

**Osc 1 at 192 kHz, all three shapes, MIDI 36-96** (`192k/osc1_*.wav`): pitch within ±0.01 cent everywhere
again. Saw as before.
- **Triangle:** odd harmonics about 5 dB below an ideal triangle's, so it is rounded. Even harmonics sit at −25
  to −30 dB, so it is slightly asymmetric.
- **Pulse width:** PW CC → `dial << 8` → design §2.2's quadratic law, **confirmed** across PW 16-127 at note 48.
  The measured high fraction is 0.0107 / 0.0347 / 0.0737 / 0.1294 / 0.2007 / 0.2871 / 0.3896 / 0.4922 against
  the law's 0.0086 / 0.0326 / 0.0719 / 0.1266 / 0.1967 / 0.2820 / 0.3828 / 0.4835.
  - The excess of 0.002-0.009 of a cycle is probably the analogue edges' slew.
  - **PW 0 is silent**: the width is 0, so there is no pulse.
  - The pulse is high for the short part: positive-going, 12.9 % at PW 64.

**LP24 cutoff law, resonance 0**, steps of 4 from 0 to 127 (`192k/filter/lp24_c*`). Measured where the response
falls 12 dB below cutoff 127's response (floor-masked):
- **Exactly one semitone per CC step**, 1.009 semitones on a fit over cutoff 8-96. The local rate is 0.98-1.01
  from 4 to 80.
- The −12 dB point is 25 Hz at cutoff 0, 257 Hz at 40, 1033 Hz at 64 and 2631 Hz at 80. Residuals are within
  ±20 cents, a gentle S-shape.
- **Above about cutoff 84 the method fails, not the filter.** The cutoff-127 reference itself rolls off there, so
  the rate seems to climb. Self-oscillation (resonance up) will measure the top of the range directly.
- The low-frequency gain is +4.5 to +4.9 dB for cutoff 20 and above. It falls once the cutoff reaches the
  bottom bands (−7.3 dB at cutoff 0).

## 2026-10-17 - LP24: cutoff law, oscillation threshold, resonance (192 kHz, `192k/filter/`)

**Self-oscillation** (`selfosc.py`): resonance 127, no input, note 60, cutoff stepped 0-127 in one capture.
- The frequency is **23.93 Hz × 2^(cutoff / 11.977)**: 1.002 semitones per step, ±11 cents residual over cutoff
  0-110. Cutoff 0 = 24.0 Hz, 40 = 242 Hz, 64 = 972 Hz, 88 = 3.89 kHz, 110 = 13.9 kHz.
- Every step from 1 to 118 rises 0.90-1.05 semitones.
- Above about 119 (22.4 kHz) the frequency stops following and flattens near 23-24 kHz. Cutoff 121-127 move it
  by less than 0.1 semitone per step.
- The level falls slowly, from −24.7 dBFS at cutoff 0 to −28.4 at 120 (volume 40). It is nearly a sine: H2 −35
  to −37 dB, H3 −46 to −51 dB.
- **TRAP: label steps by the signal, not the clock.** midisend pauses 2 ms after every message, and the capture
  starts late. In a 77-second stepped take the measurement windows slipped one whole step, which showed up as a
  "0.13 semitone step" at 68-69 and later at 102-103. Measured on its own, that region is smooth in both
  directions. `selfosc.analyse()` now tracks the frequency and takes one plateau per step.

**Oscillation threshold:** resonance **97**, the same at cutoff 40 and 88 (96 is just below).
- From 97 to 127 the oscillation level rises about 9-10 dB (−37 → −28 dBFS).

**Resonance grid**, small signal (−30 dBFS sweep), 1/24-octave smoothing:

| Res | 0 | 16 | 32 | 48 | 64 | 80 | 88 | 92 | 96 |
|---|---|---|---|---|---|---|---|---|---|
| LF gain dB (all three cutoffs alike) | 4.9 | 4.1 | −0.3 | −3.5 | −5.8 | −7.6 | −8.4 | −8.8 | −9.1 |
| Peak above LF, cutoff 40 | 0 | 0 | 0.7 | 4.1 | 8.2 | 12.2 | 14.0 | 14.7 | 19.0 |
| Peak above LF, cutoff 64 | 0 | 0 | 0 | 2.7 | 7.0 | 11.1 | 12.7 | 13.4 | 19.8 |
| Peak above LF, cutoff 88 | 0 | 0 | 0 | 1.5 | 5.7 | 10.2 | 12.1 | 12.9 | 14.6 |

- **It behaves like a 4-pole loop with global negative feedback and no bass compensation.** Reading the bass
  loss as 1 + k gives k ≈ 0, 0.1, 0.78, 1.57, 2.35, 3.12, 3.52, 3.73, 3.90 for resonance 0-96.
  - That is roughly **k ≈ 0.049 × (res − 14)**, reaching **4 at resonance 96-97**, exactly where it starts to
    oscillate (an ideal 4-pole loop oscillates at k = 4).
  - Resonance below about 16 does almost nothing.
- The peak sits at 0.91-0.94 of the self-oscillation frequency for resonance 80-92.
- The peak is lower at high cutoffs (10.2 dB at 88 against 12.2 at 40, resonance 80). An ideal 4-pole loop at
  k = 3.12 gives 13.4 dB. Extra phase from the shelf or the top roll-off is the candidate cause.
- At resonance 0, the −12 dB point relative to the bass sits at 0.96 (cutoff 40), 0.88 (64) and 0.80 (88) of
  the self-oscillation frequency. In an ideal four equal poles it would sit at 1.0. Same suspect.

## 2026-10-17 - the four modes (`192k/filter/{lp12,bp12,hp12}_c*_r*`, `selfosc_{lp12,bp12,hp12}`)

**All four modes self-oscillate at the same frequency as LP24** at resonance 127: 242.6 / 974 / 3902 Hz at
cutoff 40 / 64 / 88, against LP24's 241.9 / 972 / 3895. **One resonant 4-pole loop, with the mode choosing the
output.** The oscillation's distortion and level depend on the output:

| Mode | Level (dBFS) | H2 (dB) | H3 (dB) |
|---|---|---|---|
| LP24 | −28 | −36 | −46 |
| LP12 | −23 | −31 | −30 |
| BP12 | −27 | −32 | −22 |
| HP12 | −30 | −30 | −18 |

So each output is taken further from the last stage, and nearer the loop's saturating input.

**Responses, resonance 0, against the self-oscillation frequency fc:**

| Mode | Below fc | Above fc | Passband | Notes |
|---|---|---|---|---|
| LP24 | flat | −21 to −22 dB/oct (method-floor limited) | +4.8 dB | |
| LP12 | flat | **−11 to −12 dB/oct** | +3.1 dB | −15 dB/oct at cutoff 88 (the top roll-off adds) |
| BP12 | **+5 to +6.5 dB/oct** | **−5 to −6 dB/oct** | about −9 dB at fc | so "12" is the total, one pole each side |
| HP12 | **+10 to +11 dB/oct** | flat | **−10 dB**, about 15 dB below LP24's | |

- Resonance cuts LP and BP below the cutoff just as in LP24. **HP12's passband is unchanged by resonance**
  (−9.6 dB above 2fc at every setting), as expected for an output taken where the loop's gain has vanished.
- This is the shape of a **pole-mixing multimode on one 4-pole loop**: LP24 = stage 4, LP12 = stage 2, BP and HP
  as sums of the loop input and stages 1-2. Each output has its own gain. To be fitted (design §3a).

## 2026-10-17 - first linear filter fit (`tools/filter_fit.py`, result in `192k/filter/fit.json`)

The model: four identical one-pole stages in a loop with feedback k. The pole frequency is derived from the
measured self-oscillation frequency through the loop's phase condition, times a fitted factor beta. An optional
pole inside the loop. Each mode's output is a weighted sum of the input, the loop input and stages 1-4. A fixed
shelf and two top poles outside the loop. Magnitude only. Masked: bands within 10 dB of the method floor, and
bands more than 45 dB below the take's own peak.

**Result: 0.42 dB rms over 15 053 points in 88 takes.** Max error 7.2 dB, at resonant peaks.
- Per take: LP24/LP12/BP12 0.1-0.3 dB at low resonance, 0.4-1.0 dB at resonance 92-96. HP12 0.65-1.04 dB.
- beta = 1.063: the pole frequency sits 6 % above the self-oscillation frequency. The loop pole ran to its bound,
  so none is needed.
- Shelf: +3.0 dB below about 180-250 Hz. Top poles: 5.6 kHz and 41 kHz.
- The HP notch is reproduced. It comes from the stage-3/4 terms in the HP mix, not from an input tap (fitted ≈ 0).

**Not yet physical:**
- **LP24 is not "stage 4 alone".** The fit mixes in stages 2 and 3 (0.23 and 0.56 against 0.91), and the measured
  slope is only −21 to −22 dB/oct. Either the stages are not identical, or the LP24 output really is a mix. A
  model with a separate pole frequency per stage and LP24 = stage 4 is the next test.
- **k at high resonance comes out too low:** 3.23 at resonance 92 and 3.38 at 96, where it oscillates at 97 and an
  ideal loop needs 4. The likely cause is the measurement, not the model. The −30 dBFS sweep plus a resonant peak
  of +15 to +20 dB drives the loop to about −10 dBFS, where EXT measurements already show H3 at −19 dB. So the
  peaks are compressed. Retake resonance 80-96 at −45 dBFS to check.

**Checked: the −30 dBFS sweeps compress the resonant peak.** LP24 retaken at −45 dBFS (`lvl45_lp24_c*_r*`):

| Cutoff | Res | Peak above bass at −30 dBFS | Peak above bass at −45 dBFS | k from bass loss |
|---|---|---|---|---|
| 40 | 80 / 92 / 96 | 12.2 / 14.7 / 19.0 | 16.0 / 24.8 / 38.7 | 3.15 / 3.74 / 3.94 |
| 64 | 80 / 92 / 96 | 11.1 / 13.4 / 19.8 | 14.8 / 22.2 / 35.9 | 3.22 / 3.82 / 4.01 |
| 88 | 80 / 92 / 96 | 10.2 / 12.9 / 14.6 | 13.2 / 20.8 / 27.0 | 3.25 / 3.84 / 4.04 |

- The bass gain is identical at both levels (linear), and only the peak compresses. **k ≈ 4.0 at resonance 96**,
  so the loop is textbook: it oscillates at k = 4 and resonance 97.
- At resonance 96 and cutoff 40, an ideal loop at k = 3.94 gives 38 dB. The measurement gives 38.7.
- **The resonance is strongly level-dependent from modest inputs on.** That belongs to the nonlinear model, and is a
  large part of the sound. The fit now uses the −45 dBFS takes for resonance 80 and above.

**Refit with the −45 dBFS takes** (free output mixes): 0.46 dB rms over 14 942 points. k at resonance 96 = 3.89,
near 4. Resonance 88 still uses its −30 dBFS take, so its k (3.23) is off-trend.

**Per-stage poles, LP24 = stage 4 alone** (`filter_fit.py --stages`, `fit_stages.json`): **worse**, 0.93 dB rms.
- It needs implausible stage ratios (1 / 1.006 / 2.11 / 0.73) and k above 4 at resonance 92-96. It also loses the
  HP notch (HP 1.0-3.4 dB).
- **So four one-pole stages with LP24 at the end is not the circuit.** The free-mix fit stays the working model.
- Next hypothesis: **two 2-pole sections inside the global loop**. LP12, BP12 and HP12 would be the first
  section's outputs, and LP24 the second's.

**Rig state for every capture so far (CT, 2026-10-17): the Pulse 2's front-panel master volume knob was at
FULL.** The sound's own volume (CC57) was 40 from the first unclipped take onwards. No evidence yet that the
output stage distorts at full, but it is unchecked. Everything the nonlinearity fit relies on (the EXT harmonics,
the oscillation's H2/H3, the peak compression at −30 dBFS) could include output-stage distortion.

**Output-stage check (`tools/vol_check.py`, `volcheck/`): the master knob adds no distortion.** CT moved the
knob from full (127) to 3 o'clock (the display reads 108):
- The level falls 13.1-13.2 dB at every point (EXT −30/−20/−10 dBFS in, saw at note 48).
- H2 and H3 stay within 0.1 dB at −20 and −10 dBFS in, and every saw harmonic within 0.1 dB.
- The one bigger change (H3 −66 → −62 at −30 dBFS in) is the noise floor showing, 13 dB nearer.
- **So the distortion measured so far happens before the master knob.** Captures stay at full, for the better
  signal-to-noise ratio.
- The knob's taper is steep at the top: 127 → 108 costs 13 dB.

## 2026-10-17 - oscillator session (`/Volumes/ext-ssd/Captures/Pulse2/192k/osc/`, `tools/osc_laws.py`)

**Semitone:** CC 16-112 = −48..+48 semitones exactly (within 0.4 cent, the period quantisation at the top).

**Detune: 2/256 of a semitone per step through the pitch law** (design §2.1). It matches all 17 measured points
(CC 0-127, −50.7 to +48.5 cents) to **0.05 cent**, the interpolation error included. So detune is a pitch offset
before the period law, not a separate frequency change.

**Level (osc 1 saw, note 48, at the output):** silent at CC 0 and 8. The rest fits
`((CC − 12.6) / 114.4)^0.864` to ±0.5 dB: −26.2 dB at 16, −13.6 at 32, −5.7 at 64, −2.1 at 96. The exponent may
be partly the compression below, since level is read after the filter.

**The oscillator is a near-ideal saw. The colour comes from the path after it.** Harmonics 2-12 against an ideal
saw (1/k):

| Note | Level 127 | Level 64 | Level 32 |
|---|---|---|---|
| 48 | −1.6 … −3.2 | −1.2 … −2.1 | −1.1 … −1.9 |
| 72 | −1.1 … −5.5 | −0.5 … −2.1 | −0.3 … −0.5 |
| 84 | −1.3 … −8.7 | −0.2 … −6.9 | 0.0 … −3.0 |

- **The level dependence is saturation** after the oscillator (the filter's loop or the VCA), compressing the
  upper harmonics as the level rises. That is the earlier "curved saw", not the oscillator's shape.
- **Low notes read 2-3.5 dB under at every level:** the bass shelf (+2.9 dB below about 200 Hz) lifts the
  fundamental, not the harmonics.
- **High notes fall away at every level:** the filter's top pole (5.7 kHz) at cutoff 127.
- So the model's DCO stays an ideal saw. The drive into the filter (`OSC_INTO_FILTER`) is to be fitted so that
  level 127 against 32 reproduces this table.

## 2026-10-17 - sound backup, and cutoff modulation steps

**Sound backup** (`tools/p2dump`): 407 sounds in `iCloud Drive/Patches/Pulse2/`, as `NNN Name.syx` (137 bytes
each, checksums valid) plus `Patches.txt`, in the Voyager folder's format. Slots 406-498 never answer a request
(twice tried) while 404, 405 and 499 do, so they are taken to be empty. P499 holds "INIT".

**Cutoff modulation is a 1 kHz staircase, softened** (`tools/mod_step.py`, `modstep/modstep_s20_a100_c64`).
LFO 1 saw → cutoff (mod 1, amount 100), LFO speed 20, filter self-oscillating at cutoff 64, resonance 127, no
input. The oscillation sweeps 110 Hz → 9 kHz about every 2 s, read cycle by cycle from its zero crossings.
- Against a smooth curve the pitch deviates 0.03 semitone rms (0.09 max), so it is smooth to the ear at this rate.
- **But its rate of change repeats every 1.00 ms** (autocorrelation r ≈ 0.55 at every 1 ms lag, refined period
  0.9995 ms). So the cutoff is updated at 1 kHz, about 0.044 semitone per update at this sweep rate.
- **Each update is a glide, not a jump.** Folded on the period, the pitch moves fastest just after the update
  and slows through the millisecond. 54 % of each step happens in the first quarter: a one-pole smoothing with
  a time constant of roughly 0.3 ms.
- The 1 kHz tone in the noise floor (−96 dBFS while a note sounds) is very likely the same update clock.

## 2026-10-17 - amp envelope (`env/`, `tools/env_session.sh`, `tools/env_analyse.py`)

Osc 1 saw at note 96, filter open, amp envelope on the VCA. Every 8th value of attack, decay and release, each
held long enough, then a sustain sweep. Levels are relative to sustain 127 (−16.5 dBFS).

- **Decay and release follow one law, and it is exponential** (straight in dB). −20 dB comes at 0.47 of the
  −40 dB time, and −6 dB at 0.165 of it. Value → seconds to −40 dB:
  0:0.001 8:0.005 16:0.013 24:0.029 32:0.061 40:0.125 48:0.252 56:0.504 64:1.01 72:2.01 80:3.97 88:6.04 96:7.48
  104:9.79 112:14.0 120:27.8 127:about 45 (release reaches −20 dB at 39.8 s).
  **The time doubles every 8 steps from about 16 to 80**, grows more slowly from 88 to 112, then jumps at the top.
- **Attack is a slow-start curve, the same shape at every value**: amplitude ≈ (t/T)^2.5. The −40/−20/−6 dB
  points fall at 0.136/0.41/0.76 of the −1 dB time. Value → seconds to −1 dB:
  8:0.009 16:0.036 24:0.092 32:0.19 40:0.33 48:0.54 56:0.77 64:0.94 72:1.07 80:1.25 88:1.50 96:1.87 104:2.50
  112:3.75 120:7.5 127:more than 34 (−12 dB only at 34 s).
- **Sustain level** (dB re 127): 0:−62.7 8:−46.2 16:−40.6 24:−35.0 32:−29.8 40:−24.8 48:−20.5 56:−16.7 64:−13.4
  72:−10.7 80:−8.5 88:−6.5 96:−4.8 104:−3.4 112:−2.1 120:−0.9. Curved; to fit.
- To do: the same for the filter envelope (it will share the time laws if the two are the same generator), the
  loop and trigger modes, and whether the attack's curve is the envelope's or the VCA's response.

## 2026-10-17 - filter envelope, keytrack, triggers (`fenv/`, `tools/fenv_session.py`)

The self-oscillating filter (resonance 127, no input) turns the cutoff into a pitch.
- **Filter env amount: 2 cutoff steps per unit from 64** (72 → +16.2, 80 → +32.1, 88 → +47.9, 96 → +63.9,
  56 → −15.6, 48 → −31.3).
- **The cutoff stops at both ends:** about 25 Hz at the bottom (amounts 32 and 40 both read 25.0 Hz), and about
  cutoff 120 at the top (+80 from base 40 for amounts 104-127). No wrap-around.
- **Keytrack: 2 cutoff steps per note at full**, scaled by (value − 64)/64, and zero at **note 64** (127: +23.4
  per octave across notes 60-96).
- **Filter env attack is linear, and its decay exponential** (attack 64: +5.6/+30/+60.5 steps at 0.05/0.25/0.5 s,
  full at about 1.0 s. Decay 64: a time constant of about 0.53 s).
- **One generator, one VCA curve.** The amp envelope's (t/T)^2.5 attack and its faster decay are the same
  generator seen through the VCA's response, which is the sustain table read as a curve of E. It predicts the
  amp attack's −40/−20/−6 dB points (E 0.12/0.38/0.71 against 0.13/0.39/0.73) and the decay ratio (time constant
  0.48 s predicted, 0.53 s measured). Modelled that way (code-notes/p2Env.md).
- **Triggers:** RET1/2/3 restart the envelope on an overlapping second note, and SNG1/2 carry on (legato). What
  separates 1/2/3 is not visible in this test.
- TRAP: `mod_step.cycle_track()` used a 5 ms DC remover, which cancelled oscillations below about 100 Hz and read
  them as nonsense (+72 steps). Now 200 ms. The zero-crossing tracker also fails on the envelope sweeps, so read
  those with the STFT tracker (`selfosc.track`, 4096-point window, median-filtered).

## 2026-10-17 - paraphonic modes (`para/`, `tools/para_capture.py`)

Osc 1 shape PARA-8 (8) and PARA-4 (9), osc 1 level 100, PW 64.
- **PARA-8 has 8 voices.** An 8-note chord (48-72) gives all 8 fundamentals at −33.8 to −35.5 dB each.
- **PARA-4 has 4 voices.**
- **Stealing takes the most recent note, with fades.** A 9th note in PARA-8 (76) sounds, while 72 falls 5.6 dB
  on its way out. In PARA-4 a 5th note (62) takes 59's voice: 59 goes silent and 62 is still fading in (−42 dB
  in the 0.5-1.5 s window).
- **A PARA-8 voice is one pulse** at osc 1's width: high for 14 % of the cycle at PW 64, the 8th harmonic
  cancelled to −32 dB (the width law gives 12.7 %).
- **A PARA-4 voice is two pulses per cycle at the same pitch,** each about 12.5 % wide, at a fixed phase offset
  (at about 0.2 and 0.6 of the cycle). Two pulse oscillators per voice.
- To do: the fade law (OSC1/OSC2 ENVA FADE), what osc 2's settings do to the second pulse in PARA-4, what osc 3
  does in these modes, and the unison modes.

## 2026-10-17 - first patch validation, P000-P014 (`tools/patch_validate.py`, `patches/`)

The hardware plays each stored sound (CC 32 bank, then program change; note 48, 2 s held), and `tools/p2render`
renders the same `.syx` through the plug-in's engine. Compared: third-octave spectral shape after level-matching
(attack 0-0.3 s / sustain 0.5-1.9 s / release), and the 50 ms level envelope.

- **012 AUTOBAHN BASS (nothing unbuilt): 0.6 / 0.6 / 2.3 dB, envelope 1.8 dB.** 007 PLAIN ARP (arp off) 1.3 dB in
  the sustain.
- APW patches (006, 010, 013): 44-46 dB in the sustain, since APW plays as a saw for now.
- 009 and 014: the envelope comparison breaks down (66-72 dB), with looping envelopes and the arpeggiator.
- The rest, 4-23 dB, all use mod slots (LFOs, mod matrix), which are not built yet. 13 of the 15 use at least one.
- The feature check also flags glide on most, but glide cannot change a single held note.
- Rerun after each engine addition, as the regression measure.

## 2026-10-17 - LFO 1 (`lfo/`, `tools/lfo_session.py`)

LFO 1 → cutoff through mod slot 1, with the filter self-oscillating at cutoff 64.
- **Rate: one octave per 12 speed steps, f = 6.897 Hz × 2^((speed − 64)/12).** Every 8 steps from 24 to 127
  multiplies the rate by 1.587 (= 2^(2/3)): 0.671/1.099/1.709/2.747/4.333/6.897/10.93/17.33/27.53/43.76/69.46/110.2/
  175.0/262.1 Hz at 24..127. Speeds 0 and 8 were not measured (the windows were too short for their periods).
- **The swing falls at fast rates:** 62 steps peak to peak to speed 64, 58 at 80, 47 at 112, 39 at 127. That is
  consistent with the LFO being worked out on the 1 kHz tick and smoothed.
- **Shapes:** SINE, TRI, SAW (rising, then a drop), SQR (bipolar) and S&H as named. **The "s" variants run at
  about 1/5 of the rate** (0.336 Hz against 1.709 at speed 40), with the same shapes.
- **Mod amount is quadratic and symmetric:** swing peak to peak = **0.0610 × (amount − 64)²** steps (68: 0.98,
  72: 3.92, 80: 15.6, 88: 35.1, 96: 62.2; 56: 3.92, 32: 62.1). It clips at the cutoff range beyond about 110. So
  an LFO at ±1 moves the cutoff ±0.0305 × (amount − 64)² steps.
- To do: LFO 2 (rate, its shape, delay), the phase settings, the other targets' scaling.

## 2026-10-17 - velocity and volume (`vel/`, `tools/vel_session.py`)

- **Volume** (velocity 100, amp velocity 64), dB relative to 127: 0: −83, 8: −47.5, 16: −32.2, 24: −22.5,
  32: −16.7, 40: −12.9, 48: −10.1, 64: −6.2, 80: −3.5, 96: −1.5, 112: −0.5.
- **Amp velocity adds to volume:** effective volume = volume + velocity × (amp velocity − 64)/64, read through the
  volume law. Every point agrees to about 0.5 dB: amp velocity 0/32 at velocities 16/32/64, 96 at 16-127, 127 at
  16-127. At amp velocity 64, velocity does nothing.
- **One VCA curve:** the volume law also predicts the sustain table measured at volume 40 (sustain 64: −14.4
  predicted, −13.4 measured; 32: −30.8 against −29.8). So the level is F(envelope × effective volume).
- **Filter velocity:** cutoff += (value − 64) × velocity / 128 steps (127 at velocity 127: +62.5; 96 at 64:
  +16.2; 32 at 127: −31.2).
- AutoSleep aside: the owner reports staggering alone does not hide the wake glitches; a quiet period was added
  there.

**Patch validation, round 3** (with LFOs, mod matrix, velocity and the VCA curve). Sustain-window spectral shape,
dB (round 1 in brackets):
000 10.3 (6.7) · 001 10.9 (4.0) · 002 17.3 (12.7) · 003 22.4 (22.0) · 004 9.1 (12.9) · 005 4.0 (12.0) ·
006 46.2 (44.0, APW) · 007 4.3 (1.3) · 008 25.5 (23.6) · 009 1.7 (6.5) · 010 52.0 (46.4, APW) · 011 33.3 (32.4) ·
012 0.6 (0.6) · 013 40.8 (46.0, APW) · 014 18.0 (17.5).
- The attack windows improved most (008: 6.1 → 1.0, 011: 7.7 → 0.9, 005: 13.8 → 4.7).
- 012 still matches everywhere (release 2.3 → 1.1).
- The three "WITH DELAY" sounds (003/008/011) miss by 22-33 dB in the sustain, and nothing on the missing list
  explains it. Next to study one by one.
- Some went worse (000, 001, 002) now that velocity and the mod matrix are active. The provisional per-target
  mod scalings are the first suspect.

## 2026-10-17 - APW (`osc/apw_48_pw*`)

Osc 1 shape APW at note 48. Folded over two cycles, the high runs are 0.031 + 0.969 (PW 32), 0.125 + 0.867 (64),
0.711 + 0.289 (96), about 0.5 + 0.5 (127). **The width alternates between the PW law's w and 1 − w, cycle by
cycle.** The strongest component at PW 64 is the sub-octave (65.4 Hz for a 130.8 Hz note).

**Validation, harmonic by harmonic** (`patch_validate.py` now compares the first 24 harmonics, ignoring those
within 10 dB of the noise beside them; third-octave bands scored hum and hiss under dark, quiet sounds as
differences). rms of the level-matched harmonic difference, attack/sustain/release, dB: 003 0.5/0.4/1.9,
008 0.8/2.7/2.6, 011 0.9/2.7/2.3, 012 0.6/0.6/0.5, 001 4.0/1.0/1.9, 007 2.2/4.3/3.7, 005 6.6/4.0/5.4. What is left
is mostly the level over time (2-8 dB): envelopes and the VCA.

## 2026-10-17 - mod matrix scaling (`modtgt/`, `tools/mod_targets.py`)

LFO 1 square, speed 16, through mod slot 1. **One law for every target measured: depth = (amount − 64)² / 32
in the target's own units.**
- **Pitch** (osc 1 saw, note 60): amount 68 ±0.50, 72 ±2.00, 80 ±8.00 semitones, within 0.01. (96 and 112 ran
  outside the analysis's 100-1200 Hz search; not used.)
- **Osc 1 level** (base 64), dial steps then the level law: predicted −1.3/+1.1 dB at 80 (measured
  −1.3/+1.1), −7.3/+3.6 at 96 (−7.7/+3.6), silence/+6.0 at 112 (−54.8/+5.6, clipped at 127).
- **Cutoff** (earlier): 0.0305 × (amount − 64)² steps, the same 1/32 = 0.03125 within the measurement.
- **PW:** not settled; the duty analysis assumed the pulse's polarity and read inverted.

## 2026-10-17 - CORRECTION: the instrument numbers its sounds from P001

The display counts P001..P500; the sound request counts from 0. The backup was first named by request number,
so every file and `Patches.txt` line sat one below the display. Renamed to the display's numbering (407 files,
`Patches.txt` rewritten from the files' own names). `p2dump` and `patch_validate.py` now take display numbers,
and the capture files `patches/hw_NNN`/`p2_NNN` were renamed to match. **Read every earlier "P000-P014" in
these notes as P001-P015, "slots 406-498 empty" as P407-P499, and "P499 INIT" as P500.**

## 2026-10-17 - glide (`glide/`, `tools/glide_session.py`)

Osc 1 TRI (one clean zero crossing per cycle, low-passed at 380 Hz), NORM, 48 → 60 legato, tracked cycle by cycle.
- Rates 48/64/80 approach the note exponentially. 96 and 112 move in a straight line at 3.9 semitones a second,
  identical to each other.
- One law fits all five to 0.01-0.06 semitone rms: per millisecond, x = distance × k / 2^17 in 1/256-semitone
  units, moved by floor(x) + ceil(x) (so at least one unit a millisecond). k × 2^17 = 2^(17.129 − 0.12697 ×
  (rate + 10)) for rate ≤ 74, else 265.16 − 2.0916 × (rate + 10).
- TRAP: a saw read by zero crossings gave harmonics (84-86 'semitones'); use TRI and a low-pass.

## 2026-10-17 - program change (measured on the instrument)

Bank select (CC 32) then program change, then the edit buffer's name read back with `p2dump edit`:
bank 1 program 0 → P101 CHEAP T-BEE; bank 0 program 99 → P100; bank 0 program 100 → P100 (clamped); bank 2
program 5 → P206 TOM. So the sound is P(100 × bank + min(program, 99) + 1): 100 to a bank. The plug-in does the
same from its cache, checked offline: all four land on the file's exact parameters.

## 2026-10-17 - unison (`unison/`)

UNISON-M/-P at note 60, Unison Detune 0/32/64/127, read from a fine spectrum around the fundamental.
- **Eight oscillators, evenly spaced and symmetric:** at 32, −55.3 … +54.2 cents, 15.6 cents apart; at 64,
  −109.7 … +109.2, 31.1 apart; at 127, 62 apart (only ±93.6 and ±31.9 inside the ±150 cent window). That is
  **detune × 1.25 / 256 semitone per step.** Left and right are identical.
- **Each is a pulse at osc 1's width.** At detune 0 the harmonics show a PW 64 pulse's notch near the 8th.
- **UNISON-M** with a 60+67 chord plays only the newest note (60 at −112 dB). **UNISON-P** plays both, but 60 is
  25 dB below 67 in the 0.5-1.5 s window, so how the eight are shared is still to find.
- The level is −22.9 dBFS at detune 0 and −22.1 at 64, about 5.5 dB below a single pulse at full level.

## 2026-10-17 - sync (`sync/`)

Osc 2 saw alone (+7 semitones), osc 3 at the note and silent, note 48.
- **Off:** osc 2 at 196 Hz.
- **On:** the fundamental is osc 3's 130.8 Hz, so osc 3 is the master. Folded on osc 3's period, osc 2 makes one
  ramp (about two thirds of the period, its own length) and then **holds flat at the ramp's end** until the
  next master cycle. It is not a continuous hard sync: each master edge restarts one slave cycle.

## 2026-10-17 - drive and its curves (`drive/`)

A 1 kHz sine into EXT at −30/−20/−10 dBFS, Drive 0/32/64/96/127, per curve (CC 77 = 0..3). Output level, then H2,
H3, H5 relative to the fundamental.
- **NONE:** Drive does nothing at all. Every amount gives the same output (−31.4 / −21.6 / −13.0 dBFS) and
  harmonics. The distortion at −10 in (H3 −18.9 dB) is the path's own, with no drive.
- **TUBE:** a compressor with even harmonics. At Drive 0 the output is about 10 dB below NONE. From 32 up it
  sits near −27.5 dBFS whatever the input, so the curve limits. H2 is strong (−4 to −13 dB), which makes it
  asymmetric.
- **FUZZ:** about −28 dBFS from any input and drive, H3 near −11 dB and H5 near −16. That is close to a square
  wave (−9.5 / −14), so it is a hard symmetric clipper with high gain, even at Drive 0.
- **FX:** silent (−84 dBFS, the noise floor) at every drive and level. Still to explain: the curve may need a
  signal other than EXT, or it may not be a static curve.

## 2026-10-17 - drive, continued

- **The curve is analogue.** It selects one of the instrument's circuits by switch, and Drive is a control
  voltage. The manual: "Amplifier with saturation" at the end of the chain, and osc 3's FB is fed "from the drive
  output back to the mixer".
- **FX** is not in the manual, and is silent with the oscillators too (`osc_c3_*`), even with osc 3 routed to
  DRIVE. It is the return of a planned effects board that was never made.
- **NONE** from the saw: identical at Drive 0, 64 and 127 (`osc_c0_*`).
- **Fit** (`drive_fit.py`, a clipper with coupling and a shelf): TUBE within 12.6% of the peak, FUZZ within 10.5%.
  Checked against the saw (`osc_c1_*`, `osc_c2_*`): levels relative to NONE within 0.4-2.6 dB; TUBE's H3 15 dB
  weak, FUZZ's even harmonics 10 dB weak.
- **Engine level:** at identical settings (saw, Volume 40) the engine is **7.9 dB below** the instrument,
  −22.0 against −14.1 dBFS, even after the +10 dB output change.

## 2026-10-17 - the paraphonic voice fade (`fade/`)

PARA-8; note 36 held throughout (the amp envelope stays open), note 61 played for 1 s (its fundamental is not one
of 36's harmonics: with note 60 the measurement read the held note's 4th harmonic). Amp envelope Attack 60.
- **With the amp envelope's Release at 0, Fade does nothing:** the voice stops at once at every setting. The
  fade is "done by ENV A", as the manual says.
- **Release 70:** Fade 0-64 stop at once; 83 is gone in about 0.1 s; 100 falls 25 dB in the first 0.1 s; 127
  falls about 19 dB a second (2 s to −40 dB, a release stage near 64.5).
- **Release 40:** Fade 100 and 127 stop at once.
- The fade in does not change with Fade.
- The instrument's own display agrees with the CCs (103/104), and calls the loop values OFF / A-D / D-D as the
  manual does (the plug-in had them wrong).

## 2026-10-17 - envelope loops (`loop/`)

Amp envelope A 40, D 50, R 40, a 4 s hold, 50 ms steps.
- **A-D** (S 64): attack to full, decay to the sustain level (−13 dB), a wait there, then attack again from the
  sustain level; peaks at 0.35, 1.45, 2.5, 3.55 s: a 1.05 s cycle.
- **D-D:** decay to the sustain level, then up again to full along the decay's own curve, then down: S 32 swings
  between −30 dB and full, S 64 between −13 and full, S 96 between −5 and full; periods 1.9, 1.75, 1.6 s. The
  manual's description (full to zero, Sustain the speed) does not match.

## 2026-10-17 - APW, corrected (`osc/apw_48_pw*`)

Folding the APW captures over two cycles (rather than reading harmonic levels) shows the real shape: the first
cycle a plain 50% square at every width; the second high on [½ − w, ½] and [½ + w, 1]. PW 127 is a square; low
widths a square an octave down. P011 PLAIN ARP (APW at PW 63, LFO on the width) is almost all the octave below
on the instrument, which the old model (w / 1 − w alternating) could not make: 15 dB off in the sustain.

## 2026-10-17 - LFO phase and direction (`lfo/phase_*`)

LFO 1 into the cutoff of the self-oscillating filter, speed 40 (0.55 s) and slow shapes at 60 (1.0 s); the
Phase byte set through an edit-buffer dump (no CC reaches it). The first 0.2 s of each track is the filter's
oscillation starting and is ignored.
- **Phase:** the instrument lists FREE, RAND, 0, 90, 180, 270. SAW at 0 starts at the bottom of its ramp; 90, 180
  and 270 bring its reset forward by a quarter, half and three quarters of a period; FREE resets nothing.
- **Direction:** SAW rises with a positive amount. The fast SINE, TRI and SQR start downward (TRI at its
  midpoint going down, minimum a quarter period in; SQR low first). The slow sTRI and sSQR start upward, sSAW
  rises; sSIN came out about a fifth of a period early.
- This is the pulse-width "polarity" left open earlier: the triangle used then was a fast one, running the
  other way to the model.
- P011 runs LFO 1 at FREE with a 24 s period, so its capture caught the LFO at an unknown phase: its 15 dB sustain
  difference cannot be read as a model error until it is captured at a fixed phase.

## 2026-10-17 - output level matched

The rig's Fireface inputs are at +4 dBu (line), which is how the instrument is heard here, so the captures' dBFS
is the target. The output gain is now 3.926 (+7.9 dB), which puts the engine's saw at Volume 40 on the
instrument's −14.1 dBFS.

## 2026-10-17 - osc 3's control routings (`osc3/`)

Osc 3 a square at note 24, 24 semitones down (about 8 Hz), so its effect flips between two states.
- **VCF:** on the self-oscillating filter (cutoff 64), each edge of the square kicks the cutoff (up on the rise,
  down on the fall) and it decays back to the base in about 30 ms: the path is AC coupled, near 14 Hz. The kick
  is about 56 steps at level 127 and 12 at level 32, which is the oscillator level curve: 28 steps per unit of
  osc 3. (Folding the track on osc 3's nominal period, or taking percentiles, both misread this as a step.)
- **LEVEL2** (osc 2 saw at level 64): the two states are 7.9 dB apart at level 32 (level 64 +- level 32 in level
  units predicts 8.1), and one state is silent from level 64 up. Each state sags towards the middle: the same
  coupling.

## 2026-10-17 - P011 taken apart (`p011/`)

P011 (APW, LP12 at cutoff 11, envelope amount +23, keytrack 95, velocity 96, LFO 1 on the width) was 13 dB off in
the sustain with its LFO phase fixed. Taken apart on the instrument and the engine, by CC on the edit buffer:
- **Base cutoff alone, and with keytracking:** the spectra agree within 1-2 dB, so the low cutoff and keytracking
  are right. The engine is about 5.5 dB loud at this cutoff (the open-filter saw matches exactly): the filter's
  level near the bottom of its range is still to settle.
- **Adding velocity** (envelope amount 0): the instrument brightens a little (+2.9 dB), the engine a lot. A
  render matched the instrument with velocity worth about 9 steps where the model gave 25.
- **Why:** velocity scales the filter envelope rather than adding to the cutoff (the envelope sustains at 47 here:
  0.37 × 25 ≈ 9). The earlier velocity captures had the envelope at full, where the two are the same.
- **The pulse width in P011** (filter fully open, no envelope, velocity or keytracking; 6 s): on the instrument the
  APW starts wide and narrows steadily for the whole take; the engine started narrow and widened. The slow
  triangle starts at its top and runs down, not at its middle running up (the reading from the self-oscillating
  filter, whose start is uncertain, had it the other way). The slow sine and square likewise start at their top.
- **The slow LFO's rate** (sTRI, `lfo/slow_rate_*`): speed 4 0.0229 Hz, 16 0.0763, 32 0.2136, 48 0.6104,
  64 1.6479, 96 9.979: from 0.11 to 0.24 of the fast law, not the fixed 0.197. P011 runs speed 4 (44 s, not 24 s).
- **Phase reset timing:** two identical takes of P011 (sound sent, then the note) started the slow LFO at
  different points, so the instrument does not reset it at that note-on. When it does is still to find.
- **What restarts an LFO** (the reset routine, then two takes): the filter envelope's trigger, by its own Trigger
  mode. LFO 2 restarts there, with its delay; LFO 1 only with a fast shape. The slow shapes run free, so the two
  P011 takes (sTRI) could not start at the same point.
- **Checked on the instrument** (`lfo/reset_*`, `lfo/legato_*`; fast TRI at phase 90 on the self-oscillating
  filter): two identical takes now trace the same triangle; a legato second note with the filter envelope on SNG1
  leaves the LFO running, and on RET1 restarts it.

## 2026-10-17 - the filter's level at low cutoff, and the pulse's level (`lowcut/`, `p011/`)

- **Level against cutoff** (saw at note 36, LP12 and LP24, resonance 0, cutoffs 0-127): the engine follows the
  instrument within about 1 dB at every cutoff. P011's 5.5 dB was not the filter.
- **P011 by parts:** Amp Velocity accounted for 1.7 dB (the instrument moves 9.0 dB, the engine 10.7) and
  resonance for nothing. The rest, 4 dB, was the oscillator: APW measured 4.2 dB below the engine's at every
  width, PWM 4.4 dB, while the saw and triangle agree (`osc/` captures against renders). Pulses are now 0.61.

## 2026-10-17 - osc 3 to DRIVE (`drive_route/`)

TUBE with a quiet saw (osc 1 level 30, note 72) changes level steeply with Drive: 0 −37.4, 8 −32.4, 16 −30.0,
24 −28.8, 32 −28.2, 48 −27.7, 64 −27.5 dB. With osc 3 an 8 Hz square on DRIVE (Drive 0), the peak after each edge
read through that sweep is a kick of 14.6 / 27.4 / 59.7 drive units at osc 3 level 32 / 64 / 127; over the
oscillator level curve, about 60 per edge, so 30 per unit of osc 3. The baseline with DRIVE routing sat near
Drive 8 at every level (−32.5 dB), which is not yet explained.

## 2026-10-17 - osc 3's FB (`fb/`)

- **With a saw** (osc 1 level 64, filter open, drive off): the level FALLS as FB rises (−19.8, −22.0, −25.2,
  −27.4, −28.3 dB at 0/32/64/96/127) and the tone brightens a little: negative feedback. The engine had it positive.
  A gain of 5.7 × osc 3's level matches within 1.4 dB.
- **Alone** (no oscillators, cutoff 64): the instrument sings from FB 64, near 950 Hz, quietly (−42 to −36 dB). The
  engine at 5.7 does not; at 9.0 it sings from 96, at 758 Hz and much louder, and spoils the saw case. The
  instrument's feedback is stronger near the filter's corner than in its passband.

## 2026-10-17 - the performance controls (`perf/`)

On the instrument: bend at full throw +2.00 and −11.99 semitones with Bend Up 2 / Down 12 (the engine's law); the
mod wheel and channel pressure as mod sources on the cutoff at amount +32 raise it 15.4/31.0 and 15.2/30.6 steps
at half and full (linear; the engine gives 16.1/32, within a step); the sustain pedal holds a released note until
it is lifted. As modelled.

## 2026-10-18 - Keytrack OFF, and P004

The plug-in ignored the oscillators' Keytrack switch. The instrument adds the played note to an oscillator's pitch
with Keytrack ON, and a fixed note 60 with it OFF. P004 WITH DELAY has osc 2 OFF and gives it the key back through
PITCH FLW -> M-ACCU -> M-DELAY -> OSC2 PITCH, so osc 2 followed the keyboard twice in the engine, which is the tone
that stood out (CT). The patch validation plays only note 48, which hid it. To check on the instrument: osc 2 alone,
Keytrack OFF, at several notes (the instrument was off MIDI when this was done).

## 2026-10-18 - the arpeggiator (`96k/arp/`)

- **Tempo** (Clock at index 13, which is 3/64 - the list starts at 1/1): BPM = 46 + 2 × Tempo, from 46 to 300; every
  point of 0/8/16/32/48/64/80/96/112/127 within the timing's precision.
- **Swing:** the first of each pair of steps takes (Swing − 14)% of the two: 18/34/50/66/82% at 32/48/64/80/96;
  at 14 and 114 one of the pair has no length.
- **Modes** (a chord 48 52 55, Range 2): UP 48 52 55 60 64 67 and again; DOWN the reverse; ALT up and back down
  without repeating the ends; #UP/#DWN as UP/DOWN here (played in pitch order).
- **Clock and Step Duration** from the values the panel names (p2Arp notes §1); the step bytes' layout from the
  library (notes §2); SOFT and HARD's velocity offsets (-32, +64) are the plug-in's choice, not yet measured (notes §5).
- **Trap:** the duration and mode takes ran with the step pattern of the sound sent before (P011, whose steps are not
  the default), which made Step Duration and #ALT look wrong. A take must set the steps it assumes.

## 2026-10-18 - oversampling cost

Offline, 10.5 s at 48 kHz on this Mac: P017 UNISON PAD 0.05 / 0.07 / 0.09 s of CPU at 1x / 2x / 4x, P013 0.02 /
0.05 / 0.07 s - about 1% of real time at 4x. The setting is there for slower machines and many instances.

## 2026-10-19 - back on the instrument

- **Keytrack OFF:** osc 2 alone at notes 36/48/60/72/84: 261.6 Hz every time, C4, as built.
- **An OFF step uses up its note:** Length 4, step 2 OFF, UP over 48 52 55 gives 48·55·48, 52·48·52, 55·52·55 ...
- **The modes, with the default steps:** UP, DOWN, ALT, #UP, #DWN as built. **#ALT** goes up once and then swings
  between the top two notes (64 67 64 67 ...): kept as an anomaly.

## 2026-10-19 - CT's listening round, followed up

- **LFO rates (P005):** LFO 1 speed 44 measured 2.167 Hz (law 2.172), LFO 2 speed 38 1.526 Hz (1.536): within 0.6%.
  The faster feel CT heard is not the rate law; P005 also routes the mod wheel to LFO 1's speed and LFO 2 to Mod 1's
  amount.
- **Noise (P006):** the engine's noise was 4 dB quiet in every octave band, same spectral tilt; raised. CT heard more
  noise from the plug-in in P006, so something else in that patch adds it - open.
- **P010's release** was far shorter in the plug-in: every paraphonic voice faded by itself once the chord was
  released. Now only while other keys hold the envelope.
- **Clicks** on the bottom edge of a button were missed: the hit test used the button's rectangle, not the larger
  box draw_button draws. Fixed.

## 2026-10-19 - CT's brighter/darker patches, followed up (`brightness/`, `lowcut/`, `p001/`, `bleed/`)

- All 15 patches at notes 48/60/72 and velocities 64/100/127 against the plug-in (`tools/brightness.py`,
  summary.txt). Velocity made little difference; the gaps depended on the note.
- **The cause for P004/P007/P008/P009/P012** (sustain brighter at low notes): the LP12 and LP24 output mix leaked
  the early stages, so far above a low cutoff the response stopped falling. Refitted (p2Filter notes §6); P004,
  P007, P008 now within about a dB at every note.
- **Paraphonic level:** one PARA-8 voice is 11.6 dB and a PARA-4 voice 8.8 dB below the same pulse played mono.
- **Filter keytrack** checked on the self-oscillating filter at notes 72/84 (the only ones where the instrument still
  sings): within 0.1 step at Keytrack 127 and 95. The filter envelope's sustain level matches S/127.
- **Not bleed:** with Volume 0 (and with the filter closed too) the instrument is silent to the rig's floor. A
  reading of the high band "after the note" in P001 was still the release tail.
- **Open:** P001/P014 at note 48 are darker in the plug-in once the filter envelope has decayed (the instrument's
  brightness climbs back about 18 dB over half a second; the plug-in's does not). Not the clamp below cutoff 0, the
  envelope or keytrack (each checked alone), resonance or filter velocity.

## 2026-10-19 - P001 and the patch levels

- **P001** is not a fault: osc 1 and osc 3 beat (19 detune steps, about 1.8 s), and the instrument's free-running
  DCOs start each note at a different point of it. Both the instrument and the plug-in dip and recover; only where
  differs. The plug-in's oscillators now start at their own phases per instance.
- **Volume and Amp Velocity** checked at Volume 20/31/64/100/127 and Amp Velocity 95 at velocities 64/100/127: within
  0.6 dB everywhere.
- **Pulse level:** PWM at widths 8-127 and APW at all widths were 1.2-1.6 dB loud; 0.61 -> 0.525.
- Sums of detuned oscillators cannot be compared take by take: where a slow beat is when a take starts decides its
  level.
- **P002** (osc 3 four octaves up, on VCF): with osc 3 silent it matched within a dB; with it, 9 dB dark. The filter
  FM depth fitted to it is 125 steps per unit of osc 3, not the 28 read from the singing filter's track of an 8 Hz
  square (the track could not follow the 11 ms kicks). Now within 3 dB at notes 48, 60 and 72.

## 2026-10-19 - patch levels

The patches were 2-4 dB loud. Two causes: the oscillator level law (the engine's input saturation squeezed it: a
saw at level 16-48 came out 1-1.7 dB loud; refitted, p2Plugin notes §36) and LP12's passband (0.8-1.0 dB loud
against LP24 at every level and volume; scaled by 0.902). Volume, Amp Velocity and the amp envelope's sustain (with
Amp Velocity 95, sustain 49-127) all matched within 0.2 dB. Now within about 2 dB at notes 48/60/72, except P014
(+2.5 to +3.6) and P002 (-2.3 to -3.6). Single takes of patches with detuned oscillators move by a dB or two with
where their beat falls.

## 2026-10-19 - P006 and the filter envelope, followed up

- **Filter envelope decay** on the self-oscillating filter (amount full, Sustain 0, Decay 40 and 63), aligned on the
  note's onset: within about 3 steps throughout. (Aligned on the pitch tracker's first reading instead, the
  instrument looked 0.2 s late - the tracker starts later on it.)
- **PITCH FLW as a mod source:** at note 60, +32 depth, the instrument's cutoff fell 1.9 steps and the plug-in's
  2.0: (note - 64)/64, as built. A sweep of it read garbage on the instrument (the tracker failing, not the filter).
- **P006** above 1.6 kHz: the instrument sits a flat 8-10 dB over the rig's silence whether the noise generator is
  at 104 or 0 and osc 3 on or off - the instrument's own hiss with the VCA open, not the sound. Not modelled, on
  purpose (CT does not want converter/analogue hiss). Below 1.6 kHz two identical takes differ by up to 8 dB (its
  LFO on the width, osc 3's detuned LEVEL2 modulation), so single takes cannot settle the "more noise" CT heard;
  the plug-in's noise has since been raised 4 dB (measured with the filter open) and LP12 refitted - to listen again.

## 2026-10-19 - P006's noise, resolved

CT: too much noise in P006. With osc 3 off the plug-in's noise share matched; with osc 3 on LEVEL2 the instrument's
tone rose 11-13 dB in 200-800 Hz (osc 2 times osc 3, both near 131 Hz: a strong 2nd harmonic) and the plug-in's
did not, so the plug-in's tone sat lower against the same noise. A single window cannot judge it - osc 2 and osc 3
are 3 detune steps apart, a 6 s beat that swings that band by 10 dB - so it was compared over an 8 s note: the
instrument 10.7-25.4 (mean 17.7), the plug-in at depth 1 12.2-20.6 (13.4), at depth 3 15.3-24.8 (17.2). At 3 the
noise share over the note matches below 1.6 kHz (-43.1/-15.1 against -40.3/-15.2 dB). Also: osc 3 is louder and
less tapered than osc 1/2 (+1.5 dB at 127, +2.6 at 58; its own law now), and three identical takes of two slightly
detuned oscillators beat at different phases - the DCOs do run free.

## 2026-10-19 - P006 at C3/F3 (CT: "the filter on P006 hardware is more open")

- **Filter keytrack below the reference** (base 70 so the filter sings at every note, Keytrack 95 and 127, notes
  48-72): within 0.2 steps everywhere. Not keytrack.
- **The filter envelope decays 8% slower than the amp envelope** on the instrument: time constants at Decay 48/56/
  63/72 of 0.130/0.261/0.478/1.035 s against the engine's 0.121/0.242/0.444/0.963; the amp envelope at Decay 56/63
  matched within 2%. The filter envelope's decay and release now x1.08 (p2Env notes §6); engine 0.131/0.480.
- P006 at F3 is then within about 1.5 dB in level and 2-4 dB in brightness after the first half second. At C3, two
  takes of the instrument differ by up to 5 dB in the first second (osc 2 x osc 3's 6 s beat); after a second the
  instrument's "brightness" is its own hiss over the nearly closed filter, which is left out.
- **Reverted the LEVEL2 depth of 3** (back to 1, as measured at 8 Hz): fitted to one band of one take of a patch
  that beats over 6 s, and CT heard P006 become "spectrally very different". Kept: the filter envelope's 1.08 (four
  decay settings), osc 3's level law and the noise level (each measured directly). P006's 2nd-4th harmonics,
  averaged over 7.5 s, were 4/5/10 dB under the instrument's; osc 2's pulse at width 90 (notch at the 4th) and LP12 at
  cutoff 0-16 both match, so it is in how osc 2, osc 3 and the noise combine - open.
- **Noise was rate-dependent and squashed the oscillators** (fixed): white at the internal rate, its audible level
  rose 6 dB at a 48 kHz host over the 192 kHz renders it was calibrated in, and its ultrasonic power compressed the
  oscillators in the filter by 2.4 dB at P006's noise level (the instrument: no change). Now band-limited at 22 kHz
  with a fixed density - code-notes/p2Plugin §34. A likely part of CT's "too much noise on P006".
- **Osc 3 routed away from MIX raises the whole mix 1.8x** (measured on all four routings, osc 1, osc 2 and noise;
  compression from the filter's own saturation) and **the mix and the filter's output are AC-coupled** (5 Hz) -
  code-notes/p2Plugin §37. P006: every oscillator was 5 dB quiet, and its closed filter carried sub-audio and DC
  reading 10-17 dB loud. Found by bisecting P006's dump on the hardware, two or three takes per step.
- P006 after these, against two takes per note at C3 and F3 (20 Hz high-passed): within 2-3 dB below 1 kHz;
  1-4 kHz 4-7 dB bright in the first second and still 3-6 dB later, with the envelope gone - static, around
  resonance 41 / keytrack 95 at cutoff 0, open. The first 150 ms with the filter neutral are ~3 dB quiet, open.
  The filter envelope's 1.08 moves this by 1-2 dB only; kept.
- **"Instrument brighter" on most patches was hiss and free LFOs, not the filter.** Under a closed filter the
  instrument's 4-16 kHz is its own note-gated hiss (no harmonic structure); now a Hiss switch, off by default
  (code-notes/p2Plugin §38). Free LFOs made takes differ by up to 27 dB (P012). brightness.py now loads each sound
  with both LFO phases at 0 on both sides and renders with Hiss on: 15 patches at C3/F3, most within +-3 dB.
  Open: P001 7-12 dB dark, P005 sustain 6-7 dB dark, P003 (fuzz), P015 (+5 dB, arp HOLD), P013 -2 / P014 +2 dB level.
- The filter leak refit of the morning stands: restoring the old leak brightened P006/P009/P012 by 6-24 dB below 4 kHz.
- **The engine's oscillators were upside down and 3-5 dB dull at 3-6 kHz** (CT's own recordings of P012 reduced to
  one saw, filter open). The dullness was a 5.7 kHz pole fitted from EXT IN sweeps - the input stage's, not the
  filter's; removed, the noise keeps it as its colour. Oscillators inverted; a slew limit at the filter input fits
  the level-dependent darkening (p2Filter notes §3, p2Plugin §34, §39, §40). Saw now within 0.9 dB to 7.4 kHz
  (was 5.4 dB). tools/plotwave.py draws captures against renders; osc_analyse.read() now takes 24-bit files.
- Link (plug-in to instrument): CCs for what has one, edit-buffer dumps for the rest - p2Plugin notes §41, p2Hardware.
- **Drive from the instrument's own triangle** (no EXT IN): FUZZ refitted, 23% -> 7% of the peak for normal levels
  (p2Drive notes §3). Found: FUZZ expands below about -35 dB input (P003's sustain), TUBE's bias moves with Drive;
  both open. Both drives limit hard: TUBE and FUZZ never pass 0.08-0.10 of full scale at Volume 40.
- **Drive level sweep** (17 levels, 3 pitches, NONE/FUZZ/TUBE): both curves are static shapes that limit hard; the
  quiet-input loss is a slow settling, not a curve. Structures tried and rejected, and the two ways forward, in
  p2Drive notes §4.
- **Pitch froze at key-up** (fixed, CT on P004): mod, glide and bend on the oscillators stopped at the release - p2Plugin notes §42.
- **P004 against the instrument, C3/F3 alternating** (`p004_glide/`, LFO phases fixed): pitch identical, level +0.7 dB,
  brightness within 1 dB from 10 ms on; osc 2's delayed pitch-follow agrees note for note (the instrument's "32.2"
  between notes is mains hum, 52 Hz, under osc 2's envelope dip). Fixed: the oscillators now run from creation (a
  first note from a fresh instance thumped - a one-sided swing decaying over 40 ms). Open: the first ~4 ms of a
  note over a release - the instrument's first half-cycle is smoother; 2 ms windows on a 260 Hz wave are too noisy
  to say more (`fenv_attack/` needs redoing with Filter Velocity set: at 0 the envelope did not open).
- **LP24's stopband refitted to the instrument's noise** (no oscillator, no EXT IN): a notch and a 10 dB bump moving
  with the cutoff are gone, within ~3 dB everywhere (p2Filter notes §7). P006's noise alone and the routed gain on
  it match the instrument within ~1 dB; what is left is LP12's stopband, ~2.5 dB high at 1-2.5 kHz at cutoff 0.
