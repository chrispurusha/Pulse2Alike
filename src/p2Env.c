/*
 * Pulse2Alike - the envelope generator (both envelopes).
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
// Notes: Docs/code-notes/p2Env.md - "// notes §k" refers there.

#include <math.h>

#include "p2Env.h"

// notes §1: measured every 8 steps (findings 2026-10-17), the last column at 127
static const double kAttackToMinus1Db[17] = {
    0.0015, 0.009, 0.036, 0.092, 0.189, 0.334, 0.537, 0.771, 0.938,
    1.072,  1.254, 1.500, 1.874, 2.504, 3.749, 7.499, 56.0
};
static const double kDecayToMinus40Db[17] = {
    0.001, 0.005, 0.013, 0.029, 0.061, 0.125, 0.252, 0.504, 1.010,
    2.008, 3.973, 6.039, 7.478, 9.792, 14.04, 27.77, 79.6
};
static const double kSustainDb[17]        = {
    -999.0, -46.2, -40.6, -35.0, -29.8, -24.8, -20.5, -16.7, -13.4,
    -10.7,   -8.5,  -6.5,  -4.8,  -3.4,  -2.1,  -0.9, 0.0
};

// notes §2: the envelope levels at which the VCA curve reaches −1 dB and −40 dB, which turn the times measured
// at the output into the generator's own
#define E_AT_MINUS_1_DB     (0.955)
#define E_AT_MINUS_40_DB    (0.124)
#define IDLE_BELOW          (1e-4)
#define ARRIVED_WITHIN      (1.0 / 1024.0)     // notes §5: a loop turns when decay has got there

// Value 0..127 to a position in the tables: points every 8 steps, the last one at 127.
static double table_position(double value, int * i) {
    double v = fmin(127.0, fmax(0.0, value));

    if (v >= 120.0) {
        *i = 15;
        return (v - 120.0) / 7.0;
    }
    *i = (int)(v / 8.0);
    return (v - (*i * 8.0)) / 8.0;
}

// Between table points the times are interpolated on a log scale - they grow by ratios, not differences.
static double log_lookup(const double * table, double value) {
    int    i;
    double t = table_position(value, &i);

    return exp(log(table[i]) + (t * (log(table[i + 1]) - log(table[i]))));
}

double p2_env_attack_seconds(double value) {
    return log_lookup(kAttackToMinus1Db, value);
}

double p2_env_decay_seconds(double value) {
    return log_lookup(kDecayToMinus40Db, value);
}

double p2_env_sustain_level(double value) {
    return fmin(1.0, fmax(0.0, value / 127.0));
}

// notes §4: the VCA's curve, of envelope × volume (0..1): the measured volume law, dB relative to full
static const double kVcaDb[17] = {
    -999.0, -47.5, -32.2, -22.5, -16.7, -12.9, -10.1, -8.1, -6.2,
    -4.8,    -3.5,  -2.5,  -1.5,  -1.0,  -0.5,  -0.2, 0.0
};

double p2_vca_gain(double x) {
    int    i;
    double v  = fmin(127.0, fmax(0.0, x * 127.0));
    double t  = table_position(v, &i);

    if (v < 0.25) {
        return 0.0;
    }
    double lo = (i == 0) ? -80.0 : kVcaDb[i];

    return pow(10.0, (lo + (t * (kVcaDb[i + 1] - lo))) / 20.0);
}

// notes §2: the VCA's response to the envelope - the sustain table, read as a curve of the envelope's level
double p2_env_vca_gain(double e) {
    int    i;
    double v  = fmin(127.0, fmax(0.0, e * 127.0));
    double t  = table_position(v, &i);

    if (v < 0.5) {
        return 0.0;
    }
    double lo = (i == 0) ? -60.0 : kSustainDb[i];   // value 0 is silence; from −60 dB below 8

    return pow(10.0, (lo + (t * (kSustainDb[i + 1] - lo))) / 20.0);
}

void p2_env_reset(tP2Env * e) {
    e->stage      = eP2EnvIdle;
    e->level      = 0.0;
    e->phase      = 0.0;
    e->attackFrom = 0.0;
}

void p2_env_gate_on(tP2Env * e) {
    e->rising     = false;
    e->stage      = eP2EnvAttack;
    e->attackFrom = e->level;
    e->phase      = 0.0;
}

void p2_env_gate_off(tP2Env * e) {
    if (e->stage != eP2EnvIdle) {
        e->stage = eP2EnvRelease;
    }
}

// notes §3
double p2_env_step(tP2Env * e, double dt, double attack, double decay, double sustain, double release, tP2EnvLoop loop) {
    switch (e->stage) {
        case eP2EnvAttack:
        {
            double full = p2_env_attack_seconds(attack) / E_AT_MINUS_1_DB; // a linear ramp from 0 to 1

            e->level += dt / full;

            if (e->level >= 1.0) {
                e->level = 1.0;
                e->stage = eP2EnvDecay;
            }
            break;
        }

        case eP2EnvDecay:
        {
            double s      = p2_env_sustain_level(sustain);
            double target = e->rising ? 1.0 : s;
            double tau    = p2_env_decay_seconds(decay) / -log(E_AT_MINUS_40_DB);

            e->level = target + ((e->level - target) * exp(-dt / tau));

            // notes §5
            if (fabs(e->level - target) < ARRIVED_WITHIN) {
                if (loop == eP2LoopAttackDecay) {
                    e->stage = eP2EnvAttack;
                } else if (loop == eP2LoopDecayDecay) {
                    e->rising = !e->rising;
                }
            }
            break;
        }

        case eP2EnvRelease:
        {
            double tau = p2_env_decay_seconds(release) / -log(E_AT_MINUS_40_DB);

            e->level *= exp(-dt / tau);

            if (e->level < IDLE_BELOW) {
                e->level = 0.0;
                e->stage = eP2EnvIdle;
            }
            break;
        }

        case eP2EnvIdle:
        default:
            break;
    }
    return e->level;
}
