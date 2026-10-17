/*
 * Pulse2Alike - the LFOs.
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
// Notes: Docs/code-notes/p2Lfo.md - "// notes §k" refers there.

#ifndef __P2_LFO_H__
#define __P2_LFO_H__

#include <stdint.h>

typedef struct {
    double   phase;      // 0..1
    double   held;       // S&H's current value
    uint32_t random;     // xorshift state
} tP2Lfo;

double p2_lfo_hz(double speed);
// One step of dt seconds; shape is the instrument's list (SINE, TRI, SAW, SQR, S&H, then the slow five).
// Returns -1..+1.
double p2_lfo_step(tP2Lfo * l, double dt, double speed, int shape);

#endif // __P2_LFO_H__
