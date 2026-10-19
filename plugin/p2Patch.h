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

#ifndef __P2_PATCH_H__
#define __P2_PATCH_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "p2Params.h"

// A sound dump's bytes to normalized parameter values (parameters a sound does not carry keep theirs) and the
// sound's name. False if it is not a Pulse 2 sound dump.
bool p2_patch_from_syx(const uint8_t * data, size_t len, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]);
bool p2_patch_load_file(const char * path, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]);

#define P2_DUMP_LENGTH    (137)

bool p2_patch_read_dump(const char * path, uint8_t dump[P2_DUMP_LENGTH]);   // false unless a Pulse 2 sound dump
// notes §4: parameters back to a dump - unmodelled bytes from base (NULL: zero, addressed to the edit buffer)
void p2_patch_to_syx(const double normalized[kP2ParamCount], const uint8_t * base, const char * name, uint8_t out[P2_DUMP_LENGTH]);
bool p2_patch_save_file(const char * path, const uint8_t dump[P2_DUMP_LENGTH]);
int p2_patch_param_byte(uint32_t paramId, double normalized);   // its sound byte (= its CC value), -1 if none

// notes §2: every sound in the library folder, read once (main thread) so a program change only computes
#define P2_PATCH_SLOTS    (500)            // P001..P500, as the display numbers them

const char * p2_patch_library_folder(void);
int p2_patch_library_number(const char * path);            // "NNN Name.syx" in the library folder, else 0
int p2_patch_file_number(const char * path);               // "NNN Name.syx" in any folder -> NNN, else 0
void p2_patch_cache_load(void);
void p2_patch_cache_reload(void);                          // main thread: rescan the folder
void p2_patch_cache_store(int number, const uint8_t dump[P2_DUMP_LENGTH], const char * path);
bool p2_patch_cached(int number, double normalized[kP2ParamCount], char name[P2_SOUND_NAME_LENGTH + 1]);
const char * p2_patch_cached_path(int number);   // NULL if none; main thread
const char * p2_patch_cached_name(int number);   // NULL if none; main thread
int p2_patch_program_number(int bank, int program);

#endif // __P2_PATCH_H__
