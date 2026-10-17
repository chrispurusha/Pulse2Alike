/*
 * Pulse2Alike - the menu bar: File, Controls and Help.
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
// Notes: Docs/code-notes/p2Menu.md - "// notes §k" refers there.

#include <stdio.h>
#include <string.h>

#include "synthlibDefs.h"
#include "synthlibGlobals.h"
#include "synthlibTypes.h"
#include "synthlibVersion.h"
#include "contextMenu.h"
#include "alertDialog.h"

#include "p2Draw.h"
#include "p2Menu.h"
#include "p2Params.h"
#include "p2Patch.h"

#define BANKS            (5)
#define GROUPS           (10)    // of ten sounds, to a bank
#define GROUP_SIZE       (10)
#define ITEM             (tRgb)RGB_GREY_3
#define ITEM_DISABLED    (tRgb)RGB_GREY_5
#define END_OF_MENU      (tMenuItem){NULL, (tRgb)RGB_BLACK, NULL, 0, NULL, 0, 0.0, NULL}

// ---- File -------------------------------------------------------------------------------------------------

static void action_open(int index) {
    (void)index;
    p2_draw_open_patch();
}

static void action_save(int index) {
    (void)index;
    p2_draw_save_patch(false);
}

static void action_save_as(int index) {
    (void)index;
    p2_draw_save_patch(true);
}

static void action_init(int index) {
    (void)index;
    p2_draw_init_patch();
}

static void action_reload_library(int index) {
    (void)index;
    p2_patch_cache_reload();
}

// notes §1: the item's param is its sound number
static void action_load_number(int index) {
    p2_draw_load_number((int)gContextMenu.items[index].param);
}

static tMenuItem gBankItems[BANKS + 1];
static tMenuItem gGroupItems[BANKS][GROUPS + 1];
static tMenuItem gSoundItems[BANKS * GROUPS][GROUP_SIZE + 1];
static char      gBankLabels[BANKS][16];
static char      gGroupLabels[BANKS * GROUPS][16];
static char      gSoundLabels[BANKS * GROUPS * GROUP_SIZE][P2_SOUND_NAME_LENGTH + 8];

// notes §1: Bank > ten sounds > the sounds by name, built as the menu opens so a save or a reload shows at once
static void build_number_menu(void) {
    for (int b = 0; b < BANKS; b++) {
        snprintf(gBankLabels[b], sizeof(gBankLabels[b]), "P%03d-P%03d", (b * 100) + 1, (b + 1) * 100);

        for (int g = 0; g < GROUPS; g++) {
            int group = (b * GROUPS) + g;

            for (int s = 0; s < GROUP_SIZE; s++) {
                int          number = (group * GROUP_SIZE) + s + 1;
                const char * name   = p2_patch_cached_name(number);

                snprintf(gSoundLabels[number - 1], sizeof(gSoundLabels[0]), "%03d %s", number, (name != NULL) ? name : "-");
                gSoundItems[group][s] = (tMenuItem){
                    gSoundLabels[number - 1], (name != NULL) ? ITEM : ITEM_DISABLED, (name != NULL) ? action_load_number : NULL,
                    (uint32_t)number, NULL, 0, 0.0, NULL
                };
            }

            gSoundItems[group][GROUP_SIZE] = END_OF_MENU;
            snprintf(gGroupLabels[group], sizeof(gGroupLabels[0]), "P%03d-P%03d", (group * GROUP_SIZE) + 1, (group + 1) * GROUP_SIZE);
            gGroupItems[b][g]              = (tMenuItem){
                gGroupLabels[group], ITEM, NULL, 0, gSoundItems[group], 1, 0.0, NULL
            };
        }

        gGroupItems[b][GROUPS] = END_OF_MENU;
        gBankItems[b]          = (tMenuItem){
            gBankLabels[b], ITEM, NULL, 0, gGroupItems[b], 1, 0.0, NULL
        };
    }

    gBankItems[BANKS] = END_OF_MENU;
}

static void open_file_menu(tCoord anchor) {
    static tMenuItem items[8];
    bool             haveFile = p2_draw_has_patch_file();
    int              i        = 0;

    build_number_menu();
    items[i++] = (tMenuItem){
        "Open Patch...", ITEM, action_open, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Load Patch by Number", ITEM, NULL, 0, gBankItems, 1, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Save Patch", haveFile ? ITEM : ITEM_DISABLED, haveFile ? action_save : NULL, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Save Patch As...", ITEM, action_save_as, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Init Patch...", ITEM, action_init, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Reload Patch Library", ITEM, action_reload_library, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// ---- Controls ---------------------------------------------------------------------------------------------

static void action_drag_vertical(int index) {
    (void)index;
    synthlib_set_dial_mode(eDialModeVertical);
}

static void action_drag_horizontal(int index) {
    (void)index;
    synthlib_set_dial_mode(eDialModeHorizontal);
}

// "* " marks the one in force, as SynthEdit's Controls menu does
static void open_controls_menu(tCoord anchor) {
    static tMenuItem items[3];
    bool             horizontal = synthlib_dial_mode() == eDialModeHorizontal;

    items[0] = (tMenuItem){
        horizontal ? "Drag Dials Vertically" : "* Drag Dials Vertically", ITEM, action_drag_vertical, 0, NULL, 0, 0.0, NULL
    };
    items[1] = (tMenuItem){
        horizontal ? "* Drag Dials Horizontally" : "Drag Dials Horizontally", ITEM, action_drag_horizontal, 0, NULL, 0, 0.0, NULL
    };
    items[2] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// ---- Help -------------------------------------------------------------------------------------------------

static void action_about(int index) {
    (void)index;
    show_alert("About", synthlib_about_text("Pulse2Alike"));
}

static void open_help_menu(tCoord anchor) {
    static tMenuItem items[2];

    items[0] = (tMenuItem){
        "About Pulse2Alike...", ITEM, action_about, 0, NULL, 0, 0.0, NULL
    };
    items[1] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

static const tMenuBarItem gMenuBar[] = {
    {"File",     open_file_menu    },
    {"Controls", open_controls_menu},
    {"Help",     open_help_menu    },
    {NULL,       NULL              },
};

const tMenuBarItem * p2_menu_bar(void) {
    return gMenuBar;
}

tRectangle p2_menu_bar_rect(void) {
    return (tRectangle){{
                            0.0, 0.0
                        }, {
                            P2_CANVAS_W, P2_MENU_BAR_H
                        }
    };
}
