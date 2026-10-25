/*
 * Pulse2Alike - the digitally controlled oscillator.
 *
 * Copyright (C) 2026 Chris Turner <chris_purusha@icloud.com>
 *
 * This program is free software: you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
 * even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with this program. If
 * not, see <https://www.gnu.org/licenses/>.
 */
// Notes: Docs/code-notes/p2Dco.md - "// notes §k" refers there.

#ifndef __P2_DCO_H__
#define __P2_DCO_H__

#include <stdbool.h>
#include <stdint.h>

#define P2_DCO_CLOCK_HZ          (12000000.0)
#define P2_PITCH_PER_SEMITONE    (256)
#define P2_PITCH_MIDI_ZERO       (36 * P2_PITCH_PER_SEMITONE)   // notes §1
#define P2_PITCH_MAX             (196 * P2_PITCH_PER_SEMITONE)
#define P2_WIDTH_MAX             (0x7E00)
#define P2_WIDTH_SQUARE          (0x8000)   // notes §4: osc 3's SQR, an exact half cycle

typedef enum {
    eP2ShapePulse = 0,
    eP2ShapeSaw,
    eP2ShapeTriangle,
    eP2ShapeApw,         // notes §7: the width alternates w, 1 - w each cycle
    eP2ShapeCount
} tP2Shape;

typedef struct {
    double   phase;            // 0..1, wrapping at the main edge
    double   increment;        // cycles per sample
    double   pulseFraction;    // of the cycle, ending at the main edge
    int      cycle;            // counts main edges, for APW
    bool     syncHold;         // notes §8: synced - after one cycle, hold until the master restarts it
    bool     held;
    bool     wrapped;          // the last p2_dco_next() crossed the main edge
    tP2Shape shape;
    double   readOffset;       // notes §10: where the wave is read against the cycle's timing (synced osc 2)
    double   edgeCoef;         // notes §11: a pulse's edges, softer than the saw's
    double   edgeState;
} tP2Dco;

int32_t p2_pitch_from_midi_note(double note);
uint32_t p2_dco_period_ticks(int32_t pitch);
double p2_dco_pulse_fraction(int32_t width);   // notes §4: of the cycle the pulse is high

void p2_dco_set(tP2Dco * dco, int32_t pitch, int32_t width, tP2Shape shape, double sampleRate);
float p2_dco_next(tP2Dco * dco);
void p2_dco_restart(tP2Dco * dco);                    // the master's edge: start a new cycle now
float p2_dco_gate(const tP2Dco * dco, bool halfRate); // notes §9: a 50 % square on its edges, now

#endif // __P2_DCO_H__
