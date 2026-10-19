/*
 * Pulse2Alike - the arpeggiator.
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
// Notes: Docs/code-notes/p2Arp.md - "// notes §k" refers there.

#include <math.h>
#include <string.h>

#include "p2Arp.h"

// notes §1: the panel's clock values as steps in ticks (96 to a quarter), and its Step Durations in 1/32 of a step
static const int kClockTicks[20]   = {384, 288, 256, 192, 144, 128, 96, 72, 64, 48, 36, 32, 24, 18, 16, 12, 9, 8, 6, 4};
static const int kDurationOf32[15] = {4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512};

// notes §2: a step's byte
#define EVENT(b)    ((b) & 0x0F)
#define TIME(b)     (((b) >> 4) & 0x03)
#define GLIDE(b)    (((b) >> 6) & 0x01)

enum {
    eEvOff = 0,
    eEvSoft,
    eEvNorm,
    eEvHard,
    eEvEven,
    eEvOdd,
    eEvOctUp,
    eEvFirst,
    eEvReset
};
enum {
    eModeUp = 0,
    eModeDown,
    eModeAlt,
    eModeRand,
    eModeUpOrder,
    eModeDownOrder,
    eModeAltOrder
};

#define SOFT_VELOCITY    (-32)
#define HARD_VELOCITY    (64)
#define ORDER_MAX        (16)    // the # modes take the first 16 keys

void p2_arp_reset(tP2Arp * a) {
    memset(a, 0, sizeof(*a));
    a->sounding = -1;
    a->random   = 0x6C8E9CF5u;
}

static uint32_t next_random(tP2Arp * a) {
    a->random ^= a->random << 13;
    a->random ^= a->random >> 17;
    a->random ^= a->random << 5;
    return a->random;
}

// notes §3: the keys, either in pitch order or (the # modes) in the order played, over the octaves
static int sequence(const tP2Arp * a, const tP2ArpSettings * s, uint8_t * seq, uint8_t * vel) {
    uint8_t keys[P2_ARP_NOTES], kv[P2_ARP_NOTES];
    int     n     = a->keyCount;
    bool    order = s->mode >= eModeUpOrder;
    int     count = 0;

    if (order && (n > ORDER_MAX)) {
        n = ORDER_MAX;
    }
    memcpy(keys, a->key, (size_t)n);
    memcpy(kv, a->keyVelocity, (size_t)n);

    for (int i = 1; !order && (i < n); i++) {                 // pitch order, stable
        for (int j = i; (j > 0) && (keys[j - 1] > keys[j]); j--) {
            uint8_t t = keys[j];

            keys[j]     = keys[j - 1];
            keys[j - 1] = t;
            t           = kv[j];
            kv[j]       = kv[j - 1];
            kv[j - 1]   = t;
        }
    }

    for (int o = 0; o < s->octaves; o++) {
        for (int i = 0; i < n; i++) {
            int note = keys[i] + (12 * o);

            if ((note <= 127) && (count < 255)) {
                seq[count]   = (uint8_t)note;
                vel[count++] = kv[i];
            }
        }
    }

    int mode = order ? (s->mode - eModeUpOrder) : s->mode;    // #UP plays as UP, #DWN as DOWN, #ALT as ALT

    if (mode == eModeDown) {
        for (int i = 0; i < count / 2; i++) {
            uint8_t t = seq[i];

            seq[i]             = seq[count - 1 - i];
            seq[count - 1 - i] = t;
            t                  = vel[i];
            vel[i]             = vel[count - 1 - i];
            vel[count - 1 - i] = t;
        }
    } else if ((mode == eModeAlt) && (count > 2)) {
        for (int i = count - 2; (i > 0) && (count < 255); i--) {   // back down, the ends not repeated
            seq[count]   = seq[i];
            vel[count++] = vel[i];
        }
    }
    return count;
}

// notes §9: the next place in the sequence; #ALT on the instrument, once at the top, swings between the top two
static int next_index(const tP2Arp * a, const tP2ArpSettings * s, int count) {
    int top = (count + 2) / 2;                  // ALT's sequence: up to its top (count = 2n - 2 for n notes)

    if (s->quirks && (s->mode == eModeAltOrder) && (count > 2) && (a->index >= top - 2)) {
        return (a->index == top - 1) ? (top - 2) : (top - 1);
    }
    return (a->index + 1) % count;
}

static void end_sounding(tP2Arp * a, tP2ArpNote emit, void * user) {
    if (a->sounding >= 0) {
        emit(user, a->sounding, 0, false, false);
        a->sounding = -1;
    }
}

void p2_arp_stop(tP2Arp * a, tP2ArpNote emit, void * user) {
    end_sounding(a, emit, user);
    a->keyCount = a->keysDown = 0;
    a->running  = false;
}

void p2_arp_key(tP2Arp * a, const tP2ArpSettings * s, int note, int velocity, bool down) {
    if (down) {
        // notes §4: HOLD keeps the chord once the keys are up; a key after that starts a new one
        if ((s->active == eP2ArpHold) && (a->keysDown == 0)) {
            a->keyCount = 0;
        }
        a->keysDown++;

        if (a->keyCount < P2_ARP_NOTES) {
            a->key[a->keyCount]           = (uint8_t)note;
            a->keyVelocity[a->keyCount++] = (uint8_t)velocity;
        }
        return;
    }
    a->keysDown -= (a->keysDown > 0) ? 1 : 0;

    if (s->active == eP2ArpHold) {
        return;
    }

    for (int i = 0; i < a->keyCount; i++) {
        if (a->key[i] == note) {
            memmove(&a->key[i], &a->key[i + 1], (size_t)(a->keyCount - i - 1));
            memmove(&a->keyVelocity[i], &a->keyVelocity[i + 1], (size_t)(a->keyCount - i - 1));
            a->keyCount--;
            break;
        }
    }
}

// notes §5: one step - which note, at what velocity, for how long
static void play_step(tP2Arp * a, const tP2ArpSettings * s, double at, double clockTicks, tP2ArpNote emit, void * user) {
    uint8_t seq[256], vel[256];
    int     count = sequence(a, s, seq, vel);
    int     pos   = (int)(a->stepCount % (uint32_t)s->length);
    uint8_t b     = s->steps[pos];
    int     event = EVENT(b);
    int     note = -1, velocity = 0, offset = 0;

    if (pos == 0 && a->stepCount > 0) {
        a->cycle++;
    }

    if (count == 0) {
        return;
    }

    // notes §5: every step uses up its place in the sequence, even one that plays nothing (measured)
    if ((event == eEvOff) || (event > eEvReset) || ((event == eEvEven) && (a->cycle & 1)) || ((event == eEvOdd) && !(a->cycle & 1))) {
        a->index = next_index(a, s, count);
        return;
    }

    if (event == eEvFirst) {
        note     = a->key[0];
        velocity = a->keyVelocity[0];
    } else {
        if (event == eEvReset) {
            a->index = 0;
        }
        int i = (s->mode == eModeRand) ? (int)(next_random(a) % (uint32_t)count) : (a->index % count);

        note     = seq[i];
        velocity = vel[i];
        a->index = next_index(a, s, count);
        offset   = (event == eEvSoft) ? SOFT_VELOCITY : ((event == eEvHard) ? HARD_VELOCITY : 0);
        note    += (event == eEvOctUp) ? 12 : 0;
    }

    if ((s->accent >= 0.0) && (s->accent > velocity)) {       // notes §6
        velocity = (int)s->accent;
    }
    velocity      += offset;
    velocity       = (velocity > 127) ? 127 : velocity;

    if ((velocity <= 0) || (note > 127)) {
        return;
    }

    if (a->sounding == note) {
        end_sounding(a, emit, user);                           // the same key again: its old end must not cut it
    }
    int previous = a->sounding;

    emit(user, note, velocity, true, GLIDE(b) != 0);

    if ((previous >= 0) && (a->soundingOff <= at)) {
        emit(user, previous, 0, false, false);
    }
    a->sounding    = note;
    a->soundingOff = at + (clockTicks * kDurationOf32[s->duration] / 32.0 * (TIME(b) + 1) / 4.0);
}

// notes §7: following a host, the step grid is the host's: the first step on or after `now` (Delay moving the grid),
// and the step count from the grid, so a pattern keeps to the host's bars
static void align_to_grid(tP2Arp * a, const tP2ArpSettings * s, double now, double step) {
    double index = ceil((now / step) - s->delay);

    a->nextStep  = (index + s->delay) * step;
    a->stepCount = (uint32_t)((index > 0.0) ? index : 0.0);
    a->cycle     = a->stepCount / (uint32_t)s->length;
}

void p2_arp_run(tP2Arp * a, const tP2ArpSettings * s, double now, bool synced, tP2ArpNote emit, void * user) {
    double step = kClockTicks[(s->clock >= 0) && (s->clock < 20) ? s->clock : 12];

    if ((a->keyCount == 0) || (s->active == eP2ArpOff)) {
        if (a->running) {
            end_sounding(a, emit, user);
            a->running = false;
        }
        return;
    }

    if (!a->running) {
        a->running   = true;
        a->stepCount = a->cycle = 0;
        a->index     = 0;
        // notes §7: on its own clock it starts with the key; following a host, on the next step of its grid
        a->nextStep  = now + ((s->delay > 0.0) ? (s->delay * step) : 0.0);

        if (synced) {
            align_to_grid(a, s, now, step);
        }
    } else if (synced && (fabs(now - a->nextStep) > (4.0 * step))) {
        align_to_grid(a, s, now, step);            // the host jumped (a loop, a locate)
    }

    if ((a->sounding >= 0) && (now >= a->soundingOff)) {
        end_sounding(a, emit, user);
    }

    while (now >= a->nextStep) {
        double at   = a->nextStep;
        double pair = 2.0 * step;

        play_step(a, s, at, step, emit, user);
        // notes §8: swing - the first step of each pair takes `swing` of the two
        a->nextStep += pair * (((a->stepCount & 1) == 0) ? s->swing : (1.0 - s->swing));
        a->stepCount++;
    }
}
