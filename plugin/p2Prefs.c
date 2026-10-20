/*
 * Pulse2Alike - the plug-in's settings file.
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
// Notes: Docs/code-notes/p2Prefs.md - "// notes §k" refers there.

#include <stdbool.h>

#include "prefs.h"
#include "p2Prefs.h"

static tDialMode gDialMode = eDialModeVertical;

tDialMode p2_dial_mode(void) {
    return gDialMode;
}

void p2_set_dial_mode(tDialMode mode) {
    gDialMode = mode;
    prefs_set_int(P2_PREF_DIAL_MODE, (long)mode);
}

void p2_prefs_init(void) {
    static bool done = false;

    if (done) {
        return;
    }
    done = true;
    prefs_init("Pulse2Alike");
    long        mode = prefs_get_int(P2_PREF_DIAL_MODE, (long)eDialModeVertical);

    if ((mode == (long)eDialModeRotary) || (mode == (long)eDialModeVertical) || (mode == (long)eDialModeHorizontal)) {
        gDialMode = (tDialMode)mode;
    }
}
