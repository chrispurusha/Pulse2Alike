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

#include <fcntl.h>
#include <pthread.h>
#include <stdatomic.h>
#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <sys/file.h>
#include <unistd.h>

#include <CoreMIDI/CoreMIDI.h>

#include "synthlibMidi.h"
#include "p2Hardware.h"

#define DEVICE_NAME    "pulse"   // notes §1: matched anywhere in the port's name, any case

static MIDIClientRef gClient = 0;
static MIDIPortRef   gPort   = 0;

// The first destination (or source) whose name contains DEVICE_NAME
static MIDIEndpointRef find_endpoint(bool source) {
    ItemCount count = source ? MIDIGetNumberOfSources() : MIDIGetNumberOfDestinations();

    for (ItemCount i = 0; i < count; i++) {
        MIDIEndpointRef endpoint = source ? MIDIGetSource(i) : MIDIGetDestination(i);
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

static MIDIEndpointRef find_instrument(void) {
    return find_endpoint(false);
}

// notes §3
bool p2_hardware_claim(int * lock) {
    char path[1100];

    if (*lock >= 0) {
        return true;
    }
    snprintf(path, sizeof(path), "%s", p2_presets_path());
    snprintf(strrchr(path, '/') + 1, 32, "hardware.lock");
    p2_presets_make_folder();
    *lock = open(path, O_RDWR | O_CREAT, 0644);

    if ((*lock >= 0) && (flock(*lock, LOCK_EX | LOCK_NB) == 0)) {
        return true;
    }

    if (*lock >= 0) {
        close(*lock);
    }
    *lock = -1;
    return false;
}

void p2_hardware_release(int * lock) {
    if (*lock >= 0) {
        close(*lock);      // the lock goes with the descriptor
        *lock = -1;
    }
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

// ---- Backup - notes §4 ---------------------------------------------------------------------------------------

#define BACKUP_REPLY_TIMEOUT_S    (0.25)    // a reply comes within about 20 ms; a slot that never answers is empty
#define BACKUP_PAUSE_US           (30000)   // after each reply, as tools/p2dump paces it

static MIDIPortRef     gInPort;
static MIDIEndpointRef gInSource;
static pthread_mutex_t gReplyLock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  gReplyCond = PTHREAD_COND_INITIALIZER;
static uint8_t         gSysEx[512];
static size_t          gSysExLen;
static uint8_t         gReply[P2_DUMP_LENGTH];
static bool            gReplyReady;
static uint8_t         gBackup[P2_PATCH_SLOTS][P2_DUMP_LENGTH];
static bool            gBackupHave[P2_PATCH_SLOTS];
static _Atomic int     gBackupAsked, gBackupFound;
static _Atomic bool    gBackupRunning, gBackupFinished, gBackupCancel;
static pthread_t       gBackupThread;

static void sysex_byte(uint8_t b) {
    if (gSysExLen < sizeof(gSysEx)) {
        gSysEx[gSysExLen++] = b;
    }
}

// A sound dump arrived whole: the backup thread is waiting for it
static void sysex_done(void) {
    double values[kP2ParamCount];
    char   name[P2_SOUND_NAME_LENGTH + 1];

    if ((gSysExLen == P2_DUMP_LENGTH) && p2_patch_from_syx(gSysEx, gSysExLen, values, name)) {
        pthread_mutex_lock(&gReplyLock);
        memcpy(gReply, gSysEx, P2_DUMP_LENGTH);
        gReplyReady = true;
        pthread_cond_signal(&gReplyCond);
        pthread_mutex_unlock(&gReplyLock);
    }
    gSysExLen = 0;
}

// notes §4: MIDI 1.0 SysEx arrives as SysEx7 packets, up to six bytes each, F0 and F7 left out
static void receive(const MIDIEventList * list, void * refCon) {
    const MIDIEventPacket * packet = &list->packet[0];

    (void)refCon;

    for (UInt32 i = 0; i < list->numPackets; i++) {
        for (UInt32 w = 0; (w + 1) < packet->wordCount; w++) {
            UInt32  word0    = packet->words[w];
            UInt32  word1    = packet->words[w + 1];

            if ((word0 >> 28) != 0x3) {
                continue;
            }
            int     status   = (int)((word0 >> 20) & 0xF);
            int     count    = (int)((word0 >> 16) & 0xF);
            uint8_t bytes[6] = {(uint8_t)(word0 >> 8), (uint8_t)word0, (uint8_t)(word1 >> 24), (uint8_t)(word1 >> 16), (uint8_t)(word1 >> 8), (uint8_t)word1};

            if ((status == 0) || (status == 1)) {      // complete in one, or the start
                gSysExLen = 0;
                sysex_byte(0xF0);
            }

            for (int k = 0; (k < count) && (k < 6); k++) {
                sysex_byte(bytes[k] & 0x7F);
            }

            if ((status == 0) || (status == 3)) {      // complete in one, or the end
                sysex_byte(0xF7);
                sysex_done();
            }
            w++;
        }

        packet = MIDIEventPacketNext(packet);
    }
}

static bool wait_reply(int number, uint8_t dump[P2_DUMP_LENGTH]) {
    struct timeval  now;
    struct timespec until;
    bool            got;

    gettimeofday(&now, NULL);
    until.tv_sec  = now.tv_sec;
    until.tv_nsec = (now.tv_usec * 1000L) + (long)(BACKUP_REPLY_TIMEOUT_S * 1e9);
    until.tv_sec += until.tv_nsec / 1000000000L;
    until.tv_nsec = until.tv_nsec % 1000000000L;
    pthread_mutex_lock(&gReplyLock);

    while (!gReplyReady) {
        if (pthread_cond_timedwait(&gReplyCond, &gReplyLock, &until) != 0) {
            break;
        }
    }
    got           = gReplyReady && ((((gReply[5] << 7) | gReply[6]) + 1) == number);
    memcpy(dump, gReply, P2_DUMP_LENGTH);
    gReplyReady   = false;
    pthread_mutex_unlock(&gReplyLock);
    return got;
}

static void * backup_thread(void * unused) {
    (void)unused;

    for (int n = 1; (n <= P2_PATCH_SLOTS) && !atomic_load(&gBackupCancel); n++) {
        uint8_t request[8] = {0xF0, 0x3E, 0x16, 0x7F, 0x00, (uint8_t)((n - 1) >> 7), (uint8_t)((n - 1) & 0x7F), 0xF7};

        pthread_mutex_lock(&gReplyLock);
        gReplyReady        = false;
        pthread_mutex_unlock(&gReplyLock);

        if (p2_hardware_send(request, sizeof(request)) != eP2HardwareSent) {
            break;
        }
        gBackupHave[n - 1] = wait_reply(n, gBackup[n - 1]);

        if (gBackupHave[n - 1]) {
            atomic_fetch_add(&gBackupFound, 1);
            usleep(BACKUP_PAUSE_US);
        }
        atomic_store(&gBackupAsked, n);
    }

    MIDIPortDisconnectSource(gInPort, gInSource);
    atomic_store(&gBackupFinished, true);
    return NULL;
}

tP2HardwareResult p2_hardware_backup_start(void) {
    uint8_t           probe[1] = {0xFE};                    // active sensing: opens the output side, harmless
    tP2HardwareResult result;

    if (atomic_load(&gBackupRunning)) {
        return eP2HardwareBusy;
    }
    result    = p2_hardware_send(probe, 1);

    if (result != eP2HardwareSent) {
        return result;
    }
    gInSource = find_endpoint(true);

    if (gInSource == 0) {
        return eP2HardwareNotFound;
    }

    if (  (gInPort == 0)
       && (MIDIInputPortCreateWithProtocol(gClient, CFSTR("from Pulse 2"), kMIDIProtocol_1_0, &gInPort,
                                           ^ (const MIDIEventList * list, void * refCon) {
        receive(list, refCon);
    }) != noErr)) {
        gInPort = 0;
        return eP2HardwareNoMidi;
    }

    if (MIDIPortConnectSource(gInPort, gInSource, NULL) != noErr) {
        return eP2HardwareNoMidi;
    }
    memset(gBackupHave, 0, sizeof(gBackupHave));
    atomic_store(&gBackupAsked, 0);
    atomic_store(&gBackupFound, 0);
    atomic_store(&gBackupCancel, false);
    atomic_store(&gBackupFinished, false);
    atomic_store(&gBackupRunning, true);

    if (pthread_create(&gBackupThread, NULL, backup_thread, NULL) != 0) {
        atomic_store(&gBackupRunning, false);
        MIDIPortDisconnectSource(gInPort, gInSource);
        return eP2HardwareNoMidi;
    }
    return eP2HardwareSent;
}

bool p2_hardware_backup_poll(int * asked, int * found) {
    *asked = atomic_load(&gBackupAsked);
    *found = atomic_load(&gBackupFound);
    return atomic_load(&gBackupFinished);
}

void p2_hardware_backup_cancel(void) {
    atomic_store(&gBackupCancel, true);
}

int p2_hardware_backup_take(uint8_t dumps[P2_PATCH_SLOTS][P2_DUMP_LENGTH]) {
    int found = 0;

    if (!atomic_load(&gBackupRunning)) {
        return 0;
    }
    pthread_join(gBackupThread, NULL);
    atomic_store(&gBackupRunning, false);

    if (atomic_load(&gBackupCancel) || (atomic_load(&gBackupAsked) < P2_PATCH_SLOTS)) {
        return 0;
    }

    for (int n = 1; n <= P2_PATCH_SLOTS; n++) {
        if (gBackupHave[n - 1]) {
            memcpy(dumps[n - 1], gBackup[n - 1], P2_DUMP_LENGTH);
            found++;
        } else {
            p2_patch_init_dump(n, dumps[n - 1]);
        }
    }

    return found;
}
