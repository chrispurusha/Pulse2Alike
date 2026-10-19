/*
 * Pulse2Alike - the instrument's sound dumps (.syx) read into parameter values.
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
// Notes: Docs/code-notes/p2Patch.md - "// notes §k" refers there.

#include <dirent.h>
#include <math.h>
#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "p2Patch.h"

// notes §1
#define DATA_OFFSET    (7)

bool p2_patch_from_syx(const uint8_t * data, size_t len, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]) {
    static const uint8_t header[3] = {0xF0, 0x3E, 0x16};

    if ((len < P2_DUMP_LENGTH) || (memcmp(data, header, 3) != 0) || (data[4] != 0x10) || (data[P2_DUMP_LENGTH - 1] != 0xF7)) {
        return false;
    }
    const uint8_t *      sound     = data + DATA_OFFSET;

    for (int b = 0; b < P2_SOUND_BYTES; b++) {
        uint32_t id   = gP2SoundBytes[b].paramId;

        if (id == P2_SOUND_BYTE_UNUSED) {
            continue;
        }
        double   span = gP2Params[id].plainMax - gP2Params[id].plainMin;
        double   v    = (span > 0.0) ? ((double)(sound[b] - gP2SoundBytes[b].rawLow) / span) : 0.0;

        normalized[id] = (v < 0.0) ? 0.0 : ((v > 1.0) ? 1.0 : v);
    }

    for (int i = 0; i < P2_SOUND_NAME_LENGTH; i++) {
        uint8_t c = sound[P2_SOUND_NAME_OFFSET + i];

        name[i] = ((c >= 32) && (c < 127)) ? (char)c : ' ';
    }

    name[P2_SOUND_NAME_LENGTH] = '\0';
    return true;
}

bool p2_patch_load_file(const char * path, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]) {
    uint8_t buffer[512];
    FILE *  f   = fopen(path, "rb");

    if (f == NULL) {
        return false;
    }
    size_t  len = fread(buffer, 1, sizeof(buffer), f);

    fclose(f);
    return p2_patch_from_syx(buffer, len, normalized, name);
}

bool p2_patch_read_dump(const char * path, uint8_t dump[P2_DUMP_LENGTH]) {
    double values[kP2ParamCount] = {0};
    char   name[P2_SOUND_NAME_LENGTH + 1];
    FILE * f                     = fopen(path, "rb");

    if (f == NULL) {
        return false;
    }
    size_t len                   = fread(dump, 1, P2_DUMP_LENGTH, f);

    fclose(f);
    return (len == P2_DUMP_LENGTH) && p2_patch_from_syx(dump, len, values, name);
}

int p2_patch_param_byte(uint32_t paramId, double normalized) {
    for (int b = 0; b < P2_SOUND_BYTES; b++) {
        if (gP2SoundBytes[b].paramId == paramId) {
            long raw = lround(normalized * (gP2Params[paramId].plainMax - gP2Params[paramId].plainMin)) + gP2SoundBytes[b].rawLow;

            return (raw < 0) ? 0 : ((raw > 127) ? 127 : (int)raw);
        }
    }

    return -1;
}

// notes §4: the inverse of p2_patch_from_syx - every byte the plug-in models from its parameter, the rest from
// the dump the sound came from (or zero), and the name
void p2_patch_to_syx(const double normalized[kP2ParamCount], const uint8_t * base, const char * name, uint8_t out[P2_DUMP_LENGTH]) {
    static const uint8_t editBuffer[DATA_OFFSET] = {0xF0, 0x3E, 0x16, 0x7F, 0x10, 0x7F, 0x00};
    uint8_t *            sound                   = out + DATA_OFFSET;
    int                  sum                     = 0;

    if (base != NULL) {
        memcpy(out, base, P2_DUMP_LENGTH);
    } else {
        memset(out, 0, P2_DUMP_LENGTH);
        memcpy(out, editBuffer, DATA_OFFSET);
    }

    for (int b = 0; b < P2_SOUND_BYTES; b++) {
        uint32_t id   = gP2SoundBytes[b].paramId;

        if (id == P2_SOUND_BYTE_UNUSED) {
            continue;
        }
        double   span = gP2Params[id].plainMax - gP2Params[id].plainMin;
        long     raw  = lround(normalized[id] * span) + gP2SoundBytes[b].rawLow;

        sound[b] = (uint8_t)((raw < 0) ? 0 : ((raw > 127) ? 127 : raw));
    }

    for (int i = 0; i < P2_SOUND_NAME_LENGTH; i++) {
        char c = ((name != NULL) && (i < (int)strlen(name))) ? name[i] : ' ';

        sound[P2_SOUND_NAME_OFFSET + i] = (uint8_t)(((c >= 32) && (c < 127)) ? c : ' ');
    }

    for (int i = 1; i < P2_DUMP_LENGTH - 2; i++) {
        sum += out[i];
    }

    out[P2_DUMP_LENGTH - 2] = (uint8_t)(sum & 0x7F);
    out[P2_DUMP_LENGTH - 1] = 0xF7;
}

bool p2_patch_save_file(const char * path, const uint8_t dump[P2_DUMP_LENGTH]) {
    FILE * f = fopen(path, "wb");
    bool   ok;

    if (f == NULL) {
        return false;
    }
    ok = fwrite(dump, 1, P2_DUMP_LENGTH, f) == P2_DUMP_LENGTH;
    return (fclose(f) == 0) && ok;
}

// notes §2
#define PATCH_FOLDER    "Library/Mobile Documents/com~apple~CloudDocs/Patches/Pulse2"   // under $HOME

// notes §5: each slot is a seqlock - the main thread writes it, the audio thread copies it and keeps the copy only
// if the generation did not move (odd = being written)
static uint8_t          gCache[P2_PATCH_SLOTS][P2_DUMP_LENGTH];
static bool             gCached[P2_PATCH_SLOTS];
static _Atomic uint32_t gGeneration[P2_PATCH_SLOTS];
static char             gCachePath[P2_PATCH_SLOTS][1024];
static char             gCacheName[P2_PATCH_SLOTS][P2_SOUND_NAME_LENGTH + 1];
static pthread_once_t   gCacheOnce = PTHREAD_ONCE_INIT;

const char * p2_patch_library_folder(void) {
    static char folder[1024];

    snprintf(folder, sizeof(folder), "%s/%s", getenv("HOME") ? getenv("HOME") : "", PATCH_FOLDER);
    return folder;
}

// "NNN Name.syx" in the library folder -> NNN, otherwise 0
int p2_patch_library_number(const char * path) {
    const char * slash  = strrchr(path, '/');
    size_t       folder = strlen(p2_patch_library_folder());
    int          number;

    if ((slash == NULL) || ((size_t)(slash - path) != folder) || (strncmp(path, p2_patch_library_folder(), folder) != 0)) {
        return 0;
    }
    number = atoi(slash + 1);
    return ((number >= 1) && (number <= P2_PATCH_SLOTS) && (slash[1] >= '0') && (slash[1] <= '9')) ? number : 0;
}

static void slot_write(int number, const uint8_t * dump, const char * path) {
    int    i                     = number - 1;
    double values[kP2ParamCount] = {0};

    atomic_fetch_add(&gGeneration[i], 1);

    if (dump != NULL) {
        memcpy(gCache[i], dump, P2_DUMP_LENGTH);
        gCached[i] = p2_patch_from_syx(dump, P2_DUMP_LENGTH, values, gCacheName[i]);
        snprintf(gCachePath[i], sizeof(gCachePath[0]), "%s", path);
    } else {
        gCached[i] = false;
    }
    atomic_fetch_add(&gGeneration[i], 1);
}

static void cache_scan(void) {
    bool            seen[P2_PATCH_SLOTS] = {false};
    DIR *           dir                  = opendir(p2_patch_library_folder());
    struct dirent * e;

    while ((dir != NULL) && ((e = readdir(dir)) != NULL)) {
        char    path[1280];
        uint8_t dump[P2_DUMP_LENGTH];
        int     number;

        snprintf(path, sizeof(path), "%s/%s", p2_patch_library_folder(), e->d_name);
        number = p2_patch_library_number(path);

        if (  (number != 0) && !seen[number - 1] && (strlen(e->d_name) > 4)
           && (strcmp(e->d_name + strlen(e->d_name) - 4, ".syx") == 0) && p2_patch_read_dump(path, dump)) {
            slot_write(number, dump, path);
            seen[number - 1] = true;
        }
    }

    if (dir != NULL) {
        closedir(dir);
    }

    for (int n = 1; n <= P2_PATCH_SLOTS; n++) {
        if (!seen[n - 1] && gCached[n - 1]) {
            slot_write(n, NULL, NULL);
        }
    }
}

void p2_patch_cache_load(void) {
    pthread_once(&gCacheOnce, cache_scan);
}

void p2_patch_cache_reload(void) {
    p2_patch_cache_load();
    cache_scan();
}

void p2_patch_cache_store(int number, const uint8_t dump[P2_DUMP_LENGTH], const char * path) {
    if ((number >= 1) && (number <= P2_PATCH_SLOTS)) {
        slot_write(number, dump, path);
    }
}

// The audio thread's read: no lock, no file - a copy that is kept only if no write overlapped it
bool p2_patch_cached(int number, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]) {
    uint8_t  copy[P2_DUMP_LENGTH];
    uint32_t before, after;
    bool     cached;

    if ((number < 1) || (number > P2_PATCH_SLOTS)) {
        return false;
    }
    before = atomic_load_explicit(&gGeneration[number - 1], memory_order_acquire);

    if (before & 1u) {
        return false;
    }
    cached = gCached[number - 1];
    memcpy(copy, gCache[number - 1], P2_DUMP_LENGTH);
    atomic_thread_fence(memory_order_acquire);
    after  = atomic_load_explicit(&gGeneration[number - 1], memory_order_relaxed);
    return cached && (before == after) && p2_patch_from_syx(copy, P2_DUMP_LENGTH, normalized, name);
}

// Main thread only, as are the writes
const char * p2_patch_cached_path(int number) {
    return ((number >= 1) && (number <= P2_PATCH_SLOTS) && gCached[number - 1]) ? gCachePath[number - 1] : NULL;
}

const char * p2_patch_cached_name(int number) {
    return ((number >= 1) && (number <= P2_PATCH_SLOTS) && gCached[number - 1]) ? gCacheName[number - 1] : NULL;
}

// notes §3: as the instrument picks a sound - 100 to a bank (bank select mod 5), programs above 99 clamped
int p2_patch_program_number(int bank, int program) {
    return (100 * (bank % 5)) + ((program > 99) ? 99 : program) + 1;
}
