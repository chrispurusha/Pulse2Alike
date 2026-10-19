/*
 * Pulse2Alike - the drive: VCA saturation, after the filter.
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
// Notes: Docs/code-notes/p2Drive.md - "// notes §k" refers there.

#include <math.h>

#include "p2Drive.h"

// notes §2: the engine's level before the VCA, in the units the curves were measured in (the instrument's output
// at Volume 40, in full scale)
#define HARDWARE_UNITS_PER_ENGINE    (0.888)
#define DC_BLOCK_HZ                  (5.0)
#define DRIVE_POINTS                 (6)

typedef struct {
    double positive, negative;   // the clipper's ceilings
    double bias;
    double couplingHz;
    double shelfDirect, shelfHz; // how much passes straight, and the low-pass the rest goes through
    double gainDb[DRIVE_POINTS]; // at kDriveAt
} tCurveShape;

static const double      kDriveAt[DRIVE_POINTS] = {0.0, 16.0, 32.0, 64.0, 96.0, 127.0};

// notes §1: TUBE fitted to the instrument's 1 kHz captures (11-13% of the peak), Drive 16 interpolated; open
static const tCurveShape kTube                  = {
    0.0751, 0.0359, -0.200, 103.7, 0.000, 3123.0, {-7.25, -0.68, 5.90, 9.86, 13.18, 15.02}
};
// notes §3: FUZZ fitted to its own triangle through the open filter, two levels, six Drive settings (7% of the peak)
static const tCurveShape kFuzz                  = {0.0634, 0.0628, -0.182, 29.6, 0.653, 214, {0.96, 10.66, 12.78, 16.18, 18.35, 19.71}};

void p2_drive_init(tP2Drive * d, double rate) {
    d->rate    = rate;
    d->coupled = 0.0;
    d->lowPass = 0.0;
    d->dcBlock = 0.0;
    d->dcIn    = 0.0;
}

static double gain_db(const tCurveShape * c, double drive) {
    double d = fmin(127.0, fmax(0.0, drive));
    int    i = 0;

    while ((i < (DRIVE_POINTS - 2)) && (d > kDriveAt[i + 1])) {
        i++;
    }
    return c->gainDb[i] + (((d - kDriveAt[i]) / (kDriveAt[i + 1] - kDriveAt[i])) * (c->gainDb[i + 1] - c->gainDb[i]));
}

static double one_pole(double hz, double rate) {
    return 1.0 - exp(-2.0 * M_PI * hz / rate);
}

double p2_drive_process(tP2Drive * d, tP2DriveCurve curve, double drive, double x) {
    const tCurveShape * c;
    double              u, clipped, shaped, out;

    if (curve == eP2DriveNone) {
        return x;
    }

    if (curve == eP2DriveFx) {
        return 0.0;
    }
    c           = (curve == eP2DriveTube) ? &kTube : &kFuzz;
    u           = (x * HARDWARE_UNITS_PER_ENGINE * pow(10.0, gain_db(c, drive) / 20.0)) - d->coupled + c->bias;
    clipped     = (u >= 0.0) ? (c->positive * tanh(u / c->positive)) : (c->negative * tanh(u / c->negative));
    d->coupled += one_pole(c->couplingHz, d->rate) * clipped;
    d->lowPass += one_pole(c->shelfHz, d->rate) * (clipped - d->lowPass);
    shaped      = (c->shelfDirect * clipped) + ((1.0 - c->shelfDirect) * d->lowPass);
    // the clipper's bias leaves a DC offset; the output stage is AC coupled
    out         = shaped - d->dcBlock;
    d->dcBlock += one_pole(DC_BLOCK_HZ, d->rate) * out;
    return out / HARDWARE_UNITS_PER_ENGINE;
}
