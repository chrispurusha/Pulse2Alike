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
#include "p2Prefs.h"

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

static void action_send_to_hardware(int index) {
    (void)index;
    p2_draw_send_to_hardware();
}

static void action_load_preset(int index) {
    (void)index;
    p2_draw_load_preset_browser();
}

static void action_store_to(int index) {
    (void)index;
    p2_draw_store_preset_browser();
}

static void action_store(int index) {
    (void)index;
    p2_draw_store_preset(0);
}

static void action_revert(int index) {
    (void)index;
    p2_draw_revert_preset();
}

static void action_import(int index) {
    p2_draw_import_presets(gContextMenu.items[index].param != 0);
}

static void action_export(int index) {
    p2_draw_export_presets(gContextMenu.items[index].param != 0);
}

static void action_backup(int index) {
    (void)index;
    p2_draw_backup();
}

static void action_cancel_backup(int index) {
    (void)index;
    p2_draw_cancel_backup();
}

static void open_file_menu(tCoord anchor) {
    static tMenuItem items[8];
    bool             haveFile = p2_draw_has_patch_file();
    int              i        = 0;

    items[i++] = (tMenuItem){
        "Open Patch...", ITEM, action_open, 0, NULL, 0, 0.0, NULL
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
    items[i++] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// notes §3
static void open_presets_menu(tCoord anchor) {
    static tMenuItem items[12];
    static char      storeLabel[32], revertLabel[40];
    int              preset = p2_draw_preset();
    int              i      = 0;

    snprintf(storeLabel, sizeof(storeLabel), (preset > 0) ? "Store Preset to P%03d" : "Store Preset", preset);
    snprintf(revertLabel, sizeof(revertLabel), (preset > 0) ? "Revert to Stored P%03d" : "Revert to Stored Preset", preset);
    items[i++] = (tMenuItem){
        "Load Preset...", ITEM, action_load_preset, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        storeLabel, (preset > 0) ? ITEM : ITEM_DISABLED, (preset > 0) ? action_store : NULL, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Store Preset to...", ITEM, action_store_to, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        revertLabel, (preset > 0) ? ITEM : ITEM_DISABLED, (preset > 0) ? action_revert : NULL, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Import Presets from File...", ITEM, action_import, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Import Presets from Folder...", ITEM, action_import, 1, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Export Presets to File...", ITEM, action_export, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = (tMenuItem){
        "Export Presets to Folder...", ITEM, action_export, 1, NULL, 0, 0.0, NULL
    };
    items[i++] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// notes §4: the instrument - read only, for now: nothing here writes its memory
static void open_pulse2_menu(tCoord anchor) {
    static tMenuItem items[4];
    bool             running = p2_draw_backing_up();
    int              i       = 0;

    items[i++] = (tMenuItem){
        "Send Sound to Pulse 2", running ? ITEM_DISABLED : ITEM, running ? NULL : action_send_to_hardware, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = running ? (tMenuItem){
        "Cancel Backup", ITEM, action_cancel_backup, 0, NULL, 0, 0.0, NULL
    }
      : (tMenuItem){
        "Backup Pulse 2 to Presets...", ITEM, action_backup, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// ---- Controls ---------------------------------------------------------------------------------------------

static void action_drag_rotary(int index) {
    (void)index;
    p2_set_dial_mode(eDialModeRotary);
}

static void action_drag_vertical(int index) {
    (void)index;
    p2_set_dial_mode(eDialModeVertical);
}

static void action_drag_horizontal(int index) {
    (void)index;
    p2_set_dial_mode(eDialModeHorizontal);
}

// "* " marks the one in force, as the sibling editors' Controls menus do
static void open_controls_menu(tCoord anchor) {
    static tMenuItem items[4];
    tDialMode        mode = p2_dial_mode();

    items[0] = (tMenuItem){
        (mode == eDialModeRotary) ? "* Rotary" : "Rotary", ITEM, action_drag_rotary, 0, NULL, 0, 0.0, NULL
    };
    items[1] = (tMenuItem){
        (mode == eDialModeVertical) ? "* Vertical" : "Vertical", ITEM, action_drag_vertical, 0, NULL, 0, 0.0, NULL
    };
    items[2] = (tMenuItem){
        (mode == eDialModeHorizontal) ? "* Horizontal" : "Horizontal", ITEM, action_drag_horizontal, 0, NULL, 0, 0.0, NULL
    };
    items[3] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

// ---- Help -------------------------------------------------------------------------------------------------

static void action_about(int index) {
    (void)index;
    show_alert("About", synthlib_about_text("Pulse2Alike"));
}

// notes §2: one alert per topic; each about 11 wrapped lines at most, or it runs off the 320-high panel
#define HELP_TOPICS    (5)

static const char *const kHelpTitles[HELP_TOPICS] = {"The Panel", "Sounds and Program Changes", "Linking a Pulse 2", "Plug-in Settings", "Anomalies"};
static const char *const kHelpTexts[HELP_TOPICS]  = {
    "The pages across the top hold every control of the instrument; GLOBAL has the performance and plug-in settings.\n\n"
    "Dials: drag to turn, Shift to turn finely. Controls chooses how a drag turns them: Rotary follows the pointer "
    "round the dial, Vertical and Horizontal count its movement.\n\n"
    "Lists (shapes, filter type, modulation sources and targets) open a menu of their values on a click.\n\n"
    "The name field: click to rename the sound (14 characters, capitals); Return keeps it, Escape drops it. "
    "It reaches a file at the next save.\n\n"
    "< Prev and Next > step through the .syx files in the current sound's folder; Load... opens the file browser.",

    "The plug-in keeps 500 presets, P001-P500, as the instrument does. Program changes play them: bank select "
    "(CC 32) picks the hundred, bank 0 for P001-P100 up to bank 4 for P401-P500. < Prev and Next > step through "
    "them; P012* means the sound has been edited since.\n\n"
    "Presets > Load Preset and Store Preset to choose a slot; Store Preset puts it back where it came from, "
    "Revert discards the edits. Import from a file or a folder of \"NNN Name.syx\" files replaces all 500; "
    "Export writes them out. Pulse 2 > Backup reads all 500 from the instrument.\n\n"
    "Single sounds are .syx files: File > Open Patch, Save Patch, Save Patch As. Init Patch sets every control "
    "to its default.\n\n"
    "A host project keeps its sound as edited: reopening it does not reload the preset.",

    "Link HW (left of Prev, or Link on the GLOBAL page) makes a Pulse 2 on USB follow the sound: each change goes "
    "to it as it is made, by MIDI controller where the instrument has one and as a sound dump otherwise. A sound "
    "loaded by number also selects that number on the instrument.\n\n"
    "Set Channel on the GLOBAL page to the instrument's MIDI channel; it is remembered for every project.\n\n"
    "File > Send Sound to Pulse 2 sends the sound once. Both only ever replace the instrument's edit buffer: "
    "nothing is stored to its memory.\n\n"
    "Link works while the plug-in's window is open.",

    "Oversample: 1, 2 or 4 times the host's rate (2 by default, 4 the cleanest). Changing it clicks once.\n\n"
    "Hiss (off by default): the instrument's faint hiss while a note sounds, about 74 dB under it - its air on "
    "dark sounds.\n\n"
    "Tune (420-460 Hz) and Transpose (+-24) shift every sound. A new instance starts at 440 and 0.\n\n"
    "None of these, nor Anomalies, is saved with a sound. Diagnostic log: touch /tmp/pulse2alike-log, reload "
    "the plug-in, read /tmp/pulse2alike.log.",

    "Anomalies (on by default) keeps the quirks of the Pulse 2 this was measured on:\n\n"
    "- envelopes and modulation move the filter in softened 1 ms steps, as the instrument's do\n"
    "- the drive's FX curve is silent\n"
    "- a chord kept by one HOLD arpeggio sound starts again in the next HOLD sound\n\n"
    "Off gives the idealised instrument: everything moves smoothly, FX drives like NONE, and no chord carries "
    "over.",
};

static void action_help(int index) {
    int topic = (int)gContextMenu.items[index].param;

    show_alert(kHelpTitles[topic], kHelpTexts[topic]);
}

static void open_help_menu(tCoord anchor) {
    static tMenuItem items[HELP_TOPICS + 2];
    static char      labels[HELP_TOPICS][48];
    int              i = 0;

    for (int t = 0; t < HELP_TOPICS; t++) {
        snprintf(labels[t], sizeof(labels[t]), "%s...", kHelpTitles[t]);
        items[i++] = (tMenuItem){
            labels[t], ITEM, action_help, (uint32_t)t, NULL, 0, 0.0, NULL
        };
    }

    items[i++] = (tMenuItem){
        "About Pulse2Alike...", ITEM, action_about, 0, NULL, 0, 0.0, NULL
    };
    items[i++] = END_OF_MENU;
    open_context_menu(anchor, items, 0, 0.0);
}

static const tMenuBarItem gMenuBar[] = {
    {"File",     open_file_menu    },
    {"Presets",  open_presets_menu },
    {"Pulse 2",  open_pulse2_menu  },
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
