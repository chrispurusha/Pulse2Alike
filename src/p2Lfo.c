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

#include <math.h>

#include "p2Lfo.h"

// notes §1
#define HZ_AT_64            (6.897)
#define SPEED_PER_OCTAVE    (12.0)
#define SLOW_RATIO          (0.197)    // the "s" shapes
#define SHAPE_COUNT_FAST    (5)

double p2_lfo_hz(double speed) {
    return HZ_AT_64 * pow(2.0, (speed - 64.0) / SPEED_PER_OCTAVE);
}

static double next_random(tP2Lfo * l) {
    if (l->random == 0) {
        l->random = 0x2545F491u;
    }
    l->random ^= l->random << 13;
    l->random ^= l->random >> 17;
    l->random ^= l->random << 5;
    return ((double)l->random / 2147483648.0) - 1.0;
}

// notes §2
double p2_lfo_step(tP2Lfo * l, double dt, double speed, int shape) {
    int    base = shape % SHAPE_COUNT_FAST;
    double hz   = p2_lfo_hz(speed) * ((shape >= SHAPE_COUNT_FAST) ? SLOW_RATIO : 1.0);
    double p    = l->phase + (hz * dt);

    if (p >= 1.0) {
        p      -= floor(p);
        l->held = next_random(l);
    }
    l->phase = p;

    switch (base) {
        case 0:  return sin(2.0 * M_PI * p);

        case 1:  return (p < 0.25) ? (4.0 * p) : ((p < 0.75) ? (2.0 - (4.0 * p)) : ((4.0 * p) - 4.0));

        case 2:  return (2.0 * p) - 1.0;

        case 3:  return (p < 0.5) ? 1.0 : -1.0;

        default: return l->held;
    }
}
