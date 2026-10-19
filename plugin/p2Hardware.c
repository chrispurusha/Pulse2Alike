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
// Notes: Docs/code-notes/p2Hardware.md - "// notes §k" refers there.

#include <string.h>
#include <strings.h>

#include <CoreMIDI/CoreMIDI.h>

#include "synthlibMidi.h"
#include "p2Hardware.h"

#define DEVICE_NAME    "pulse"   // notes §1: matched anywhere in the port's name, any case

static MIDIClientRef gClient = 0;
static MIDIPortRef   gPort   = 0;

static MIDIEndpointRef find_instrument(void) {
    ItemCount count = MIDIGetNumberOfDestinations();

    for (ItemCount i = 0; i < count; i++) {
        MIDIEndpointRef endpoint = MIDIGetDestination(i);
        CFStringRef     name     = NULL;
        char            text[256];

        if ((MIDIObjectGetStringProperty(endpoint, kMIDIPropertyDisplayName, &name) != noErr) || (name == NULL)) {
            continue;
        }
        bool            found    = CFStringGetCString(name, text, sizeof(text), kCFStringEncodingUTF8) && (strcasestr(text, DEVICE_NAME) != NULL);

        CFRelease(name);

        if (found) {
            return endpoint;
        }
    }

    return 0;
}

tP2HardwareResult p2_hardware_send(const uint8_t * data, uint32_t length) {
    if (gPort == 0) {
        if (  (MIDIClientCreate(CFSTR("Pulse2Alike"), NULL, NULL, &gClient) != noErr)
           || (MIDIOutputPortCreate(gClient, CFSTR("to Pulse 2"), &gPort) != noErr)) {
            gPort = 0;
            return eP2HardwareNoMidi;
        }
        synthlib_midi_set_out_port(gPort);
    }
    MIDIEndpointRef dest = find_instrument();

    if (dest == 0) {
        return eP2HardwareNotFound;
    }
    return synthlib_midi_send_to(data, length, dest) ? eP2HardwareSent : eP2HardwareNoMidi;
}

tP2HardwareResult p2_hardware_send_to_edit_buffer(uint8_t dump[P2_DUMP_LENGTH]) {
    int sum = 0;

    // notes §2: always the edit buffer, whatever slot the dump came from - a slot number would store it to flash
    dump[5]                  = 0x7F;
    dump[6]                  = 0x00;

    for (int i = 1; i < (P2_DUMP_LENGTH - 2); i++) {
        sum += dump[i];
    }

    dump[P2_DUMP_LENGTH - 2] = (uint8_t)(sum & 0x7F);
    return p2_hardware_send(dump, P2_DUMP_LENGTH);
}
