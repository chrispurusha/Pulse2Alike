/*
 * Pulse2Alike - the sound, sent to the instrument's edit buffer over USB MIDI.
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

#ifndef __P2_HARDWARE_H__
#define __P2_HARDWARE_H__

#include <stdint.h>

#include "p2Patch.h"

typedef enum {
    eP2HardwareSent,
    eP2HardwareNotFound,   // no MIDI destination with "Pulse" in its name
    eP2HardwareNoMidi,     // CoreMIDI refused the client, the port or the send
    eP2HardwareBusy,       // notes §3: another instance owns the instrument
} tP2HardwareResult;

// notes §3: one instance on the machine owns the instrument - an exclusive flock() on hardware.lock, released by
// the system if the owner goes. *lock is the instance's descriptor, -1 when it holds nothing
bool p2_hardware_claim(int * lock);
void p2_hardware_release(int * lock);

// Any message, to the instrument
tP2HardwareResult p2_hardware_send(const uint8_t * data, uint32_t length);

// Readdresses the dump to the edit buffer (7F 00), fixes its checksum and sends it; never writes a slot
tP2HardwareResult p2_hardware_send_to_edit_buffer(uint8_t dump[P2_DUMP_LENGTH]);

// notes §4: Backup - every sound read from the instrument, one request at a time on a thread of its own. Only
// requests are sent: nothing on the instrument changes. The caller holds the lock throughout
tP2HardwareResult p2_hardware_backup_start(void);
bool p2_hardware_backup_poll(int * asked, int * found);                     // true once finished (or cancelled)
void p2_hardware_backup_cancel(void);
int p2_hardware_backup_take(uint8_t dumps[P2_PATCH_SLOTS][P2_DUMP_LENGTH]); // after the poll says finished:
                                                                            // the sounds read, INIT elsewhere
                                                                            // (0 if cancelled)

#endif // __P2_HARDWARE_H__
