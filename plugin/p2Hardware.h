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
} tP2HardwareResult;

// Any message, to the instrument
tP2HardwareResult p2_hardware_send(const uint8_t * data, uint32_t length);

// Readdresses the dump to the edit buffer (7F 00), fixes its checksum and sends it; never writes a slot
tP2HardwareResult p2_hardware_send_to_edit_buffer(uint8_t dump[P2_DUMP_LENGTH]);

#endif // __P2_HARDWARE_H__
