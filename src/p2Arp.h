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

#ifndef __P2_ARP_H__
#define __P2_ARP_H__

#include <stdbool.h>
#include <stdint.h>

#define P2_ARP_NOTES                (32)
#define P2_ARP_STEPS                (16)
#define P2_ARP_TICKS_PER_QUARTER    (96.0)

typedef enum {
    eP2ArpOff = 0,
    eP2ArpOn,
    eP2ArpHold
} tP2ArpActive;

// The sound's arpeggiator settings, as the parameters hold them (lists as their index).
typedef struct {
    int     active;            // tP2ArpActive
    int     mode;              // UP, DOWN, ALT, RAND, #UP, #DWN, #ALT
    int     octaves;           // 1..10
    int     clock;             // 0..19, 1/1 .. 1/96
    int     duration;          // 0..14, 12.5% .. 1600%
    double  swing;             // the first step's share of a pair, 0..1 (0.5 straight)
    double  delay;             // -0.5..+0.5 of a step
    int     length;            // 1..16
    uint8_t steps[P2_ARP_STEPS];
    double  accent;            // the accent source, 0..127; negative when none
    bool    quirks;            // the instrument's own oddities (Anomalies)
} tP2ArpSettings;

typedef void (*tP2ArpNote)(void * user, int note, int velocity, bool on, bool glide);

typedef struct {
    uint8_t  key[P2_ARP_NOTES];        // in the order they came
    uint8_t  keyVelocity[P2_ARP_NOTES];
    int      keyCount;
    int      keysDown;
    bool     running;
    double   nextStep;                 // in ticks, on the caller's clock
    uint32_t stepCount;                // since the start: which half of a swing pair, and the pattern step
    uint32_t cycle;                    // pattern passes, for EVEN and ODD
    int      index;                    // in the note sequence
    int      sounding;                 // the note playing, -1 none
    double   soundingOff;              // when it ends, in ticks
    uint32_t random;
} tP2Arp;

void p2_arp_reset(tP2Arp * a);
void p2_arp_key(tP2Arp * a, const tP2ArpSettings * s, int note, int velocity, bool down);
// Advance to `now` (ticks, 96 to a quarter note): plays the steps that fall due. synced: steps keep to the grid of
// the caller's clock (a host's beats) rather than starting from the first key.
void p2_arp_run(tP2Arp * a, const tP2ArpSettings * s, double now, bool synced, tP2ArpNote emit, void * user);
void p2_arp_stop(tP2Arp * a, tP2ArpNote emit, void * user);   // ends what is sounding and forgets the keys

#endif // __P2_ARP_H__
