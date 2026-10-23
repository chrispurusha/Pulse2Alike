/*
 * Pulse2Alike - the editor panel.
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
// Notes: Docs/code-notes/p2Draw.md - "// notes §k" refers there.

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "p2Draw.h"
#include "p2Hardware.h"

#include "synthlibDefs.h"
#include "synthlibGlobals.h"
#include "geometry.h"
#include "synthlibHost.h"
#include "synthlibTypes.h"
#include "utilsGraphics.h"
#include "renderBackend.h"
#include "contextMenu.h"
#include "fileBrowser.h"
#include "bankBrowser.h"
#include "alertDialog.h"
#include "menuBar.h"
#include "synthlibPopups.h"
#include "synthlibGlobals.h"

#include "p2Menu.h"
#include "p2Params.h"
#include "p2Patch.h"
#include "p2Prefs.h"

#define GL_SILENCE_DEPRECATION    1
#include <GLFW/glfw3.h>           // the key constants SynthLib's popups speak

#define FONT_PATH                 "/System/Library/Fonts/Supplemental/Arial.ttf"
#define FONT_PRELOAD_SIZE         (16.0)

#define MAX_PARAMS                (128)
#define MAX_PLACED                (64)
#define MAX_PAGES                 (16)
#define MARGIN_X                  (16.0)
#define TITLE_Y                   (30.0)     // below the menu bar
#define TAB_Y                     (58.0)
#define TAB_H                     (14.0)
#define TAB_GAP                   (6.0)
#define PAGE_Y                    (90.0)
#define ROW_H                     (112.0)
#define SECTION_GAP               (16.0)
#define CONTROL_W                 (58.0)
#define DIAL_SIZE                 (40.0)
#define LABEL_H                   (11.0)
#define HEADING_TO_DIAL           (34.0)
#define BUTTON_H                  (12.0)
#define PATCH_BAR_X               (300.0)
#define PATCH_BUTTON_H            (14.0)
#define NAME_FIELD_W              (128.0)    // 14 capitals
#define FILE_LABEL_CHARS          (26)
#define MENU_BG                   {0.22, 0.22, 0.25}
#define MENU_MAX                  (32)
#define MENU_CELL_W               (96.0)
#define MENU_ROWS_PER_COLUMN      (8)

typedef struct {
    const tP2Control * control;
    const tP2Section * section;
    tRectangle         dial;          // the dial's square; a choice's button sits across its middle
    double             x;             // the control's column
} tPlaced;

typedef struct {
    const tP2Section * section;
    double             x, y, w;
} tPlacedSection;

static const tP2Page *      gPages;
static uint32_t             gPageCount;
static uint32_t             gPage;
static double               gValue[MAX_PARAMS]; // normalized, as the host holds them
static bool                 gFontReady;
static tCoord               gMouse;

static tPlaced              gPlaced[MAX_PLACED];
static uint32_t             gPlacedCount;
static tPlacedSection       gPlacedSections[MAX_PLACED];
static uint32_t             gPlacedSectionCount;
static tRectangle           gTabs[MAX_PAGES];

// the dial being dragged; its value runs unrounded while it moves
static const tP2Control *   gGrabbed;
static double               gGrabValue;
static tRectangle           gGrabDial;          // the grabbed dial's square, for a rotary drag

// notes §2: the open value menu - which control it sets, and what was chosen
static const tP2Control *   gMenuFor;
static int                  gMenuChoice = -1;
static tMenuItem            gMenuItems[MENU_MAX + 1];

// notes §4: the patch bar
static const tP2PatchHost * gHost;
static void *               gUser;
static char                 gPatchPath[1024];
static int                  gPreset;
static bool                 gLinkBusy;
static bool                 gBackupRunning;
static int                  gBackupAsked, gBackupFound;
static bool                 gPresetEdited;
static tRectangle           gPrevRect, gNextRect, gLoadRect, gNameRect, gLinkRect;

// notes §6: the sound's name, edited in place as SynthEdit's program name is
static struct {
    bool     active;
    char     buffer[P2_SOUND_NAME_LENGTH + 1];
    uint32_t cursor;
}                           gNameEdit;

static void menu_action(int index) {
    gMenuChoice = index;
}

static void mouse_coord(tCoord * coord) {
    if (coord != NULL) {
        *coord = gMouse;
    }
}

static bool pointer_captured(void) {
    return gGrabbed != NULL;
}

void p2_draw_init(void) {
    synthlib_host_init((tSynthLibHost){.mouseCoord = mouse_coord, .pointerCaptured = pointer_captured});
    synthlib_popups_set_menu_bar(p2_menu_bar(), p2_menu_bar_rect);
    gFontReady = preload_glyph_textures(FONT_PATH, FONT_PRELOAD_SIZE);
}

void p2_draw_set_pages(const tP2Page * pages, uint32_t count) {
    gPages     = pages;
    gPageCount = (count < MAX_PAGES) ? count : MAX_PAGES;

    if (gPage >= gPageCount) {
        gPage = 0;
    }
}

void p2_draw_set_value(uint32_t paramId, double normalized) {
    if (paramId < MAX_PARAMS) {
        gValue[paramId] = normalized;
    }
}

void p2_draw_set_mouse(double x, double y) {
    gMouse.x = x;
    gMouse.y = y;
    (void)handle_file_browser_mouse_move(gMouse);
}

bool p2_draw_menu_active(void) {
    return gContextMenu.active || synthlib_popups_modal_active();
}

void p2_draw_set_host(const tP2PatchHost * host) {
    gHost = host;
}

void p2_draw_set_user(void * user) {
    gUser = user;
}

void p2_draw_set_patch(const char * path) {
    snprintf(gPatchPath, sizeof(gPatchPath), "%s", (path != NULL) ? path : "");
}

static void patch_folder(char * out, size_t len) {
    if (gPatchPath[0] != '\0') {
        snprintf(out, len, "%s", gPatchPath);
        char * slash = strrchr(out, '/');

        if (slash != NULL) {
            *slash = '\0';
            return;
        }
    }
    snprintf(out, len, "%s", p2_patch_sounds_folder());
}

static void load(const char * path) {
    if ((path != NULL) && (gHost != NULL)) {
        gHost->load(gUser, path);
        p2_draw_set_patch(path);
    }
}

void p2_draw_set_preset(int number, bool edited) {
    gPreset       = number;
    gPresetEdited = edited;
}

int p2_draw_preset(void) {
    return gPreset;
}

static void load_preset(int number) {
    if ((gHost != NULL) && (gUser != NULL)) {
        gHost->loadPreset(gUser, number);
        gPreset       = number;
        gPresetEdited = false;
        p2_draw_set_patch("");
    }
}

// notes §4: Prev/Next step through P001-P500 and wrap, as the instrument's buttons do; from a numbered file, from
// its number; from any other, Next is P001
static void step_patch(int direction) {
    int from = (gPreset != 0) ? gPreset : p2_patch_file_number(gPatchPath);

    if (from == 0) {
        from = (direction > 0) ? 0 : 1;
    }
    load_preset((((from - 1 + direction) % P2_PATCH_SLOTS) + P2_PATCH_SLOTS) % P2_PATCH_SLOTS + 1);
}

static void on_file_chosen(const char * path) {
    load(path);
}

static const char * browser_start(void) {
    static char folder[1024];

    patch_folder(folder, sizeof(folder));
    return folder;
}

// ---- what the menus ask for (p2Menu.c) - notes §5 ----------------------------------------------------------

void p2_draw_open_patch(void) {
    set_file_browser_start_directory_provider(browser_start);
    open_file_browser_read(on_file_chosen);
}

static int gStoreTo;

static void on_store_confirmed(bool confirmed) {
    char failed[1200];

    if (!confirmed || (gHost == NULL) || (gUser == NULL)) {
        return;
    }

    if (gHost->storePreset(gUser, gStoreTo)) {
        gPreset       = gStoreTo;
        gPresetEdited = false;
        p2_draw_set_patch("");
        return;
    }
    snprintf(failed, sizeof(failed), "Could not write %s", p2_presets_path());
    show_alert("Store Preset", failed);
}

// notes §4: always confirmed, naming what the slot holds now
void p2_draw_store_preset(int number) {
    static char  message[160];
    const char * name = ((gHost != NULL) && (gUser != NULL)) ? gHost->name(gUser) : "";

    gStoreTo = (number > 0) ? number : gPreset;

    if ((gStoreTo < 1) || (gStoreTo > P2_PATCH_SLOTS)) {
        return;
    }
    snprintf(message, sizeof(message), "Store \"%s\" to P%03d, replacing \"%s\"?", name, gStoreTo, p2_presets_name(gStoreTo));
    show_confirm("Store Preset", message, "Store", on_store_confirmed);
}

// ---- choosing a slot - notes §4: SynthLib's bank browser, as SynthEdit and G2Alike choose one -----------------

static tBankBrowserItem gSlotItems[P2_PATCH_SLOTS];
static char             gSlotNames[P2_PATCH_SLOTS][P2_SOUND_NAME_LENGTH + 8];

static void fill_slot_items(void) {
    p2_presets_refresh();

    for (int n = 1; n <= P2_PATCH_SLOTS; n++) {
        snprintf(gSlotNames[n - 1], sizeof(gSlotNames[0]), "P%03d %s", n, p2_presets_name(n));
        gSlotItems[n - 1] = (tBankBrowserItem){
            gSlotNames[n - 1], 0, (uint32_t)(((n - 1) / 100) + 1), (uint32_t)(((n - 1) % 100) + 1)
        };
    }
}

static int slot_number(uint32_t bank1Indexed, uint32_t location1Indexed) {
    return (int)(((bank1Indexed - 1) * 100) + location1Indexed);
}

static void on_load_slot(bool confirmed, uint32_t bank1Indexed, uint32_t location1Indexed) {
    if (confirmed) {
        load_preset(slot_number(bank1Indexed, location1Indexed));
    }
}

static void on_store_slot(bool confirmed, uint32_t bank1Indexed, uint32_t location1Indexed) {
    if (confirmed) {
        p2_draw_store_preset(slot_number(bank1Indexed, location1Indexed));
    }
}

void p2_draw_load_preset_browser(void) {
    fill_slot_items();
    open_bank_browser("Load Preset", "P001-P500, as banks 1-5 of 100.", "Load", gSlotItems, P2_PATCH_SLOTS, NULL, 0, on_load_slot);
}

void p2_draw_store_preset_browser(void) {
    fill_slot_items();
    open_bank_browser("Store Preset", "The slot to store the sound as it is now into.", "Store...", gSlotItems, P2_PATCH_SLOTS, NULL, 0,
                      on_store_slot);
}

// ---- Backup Pulse 2 to Presets - notes §11 ---------------------------------------------------------------

void p2_draw_set_backup(bool running, int asked, int found) {
    gBackupRunning = running;
    gBackupAsked   = asked;
    gBackupFound   = found;
}

bool p2_draw_backing_up(void) {
    return gBackupRunning;
}

static void on_backup_confirmed(bool confirmed) {
    if (confirmed && (gHost != NULL) && (gUser != NULL)) {
        int result = gHost->backup(gUser);

        if (result == eP2HardwareSent) {
            gBackupRunning = true;
            gBackupAsked   = gBackupFound = 0;
        } else {
            p2_draw_hardware_problem(result);
        }
    }
}

void p2_draw_backup(void) {
    show_confirm("Backup Pulse 2 to Presets",
                 "Read all 500 sounds from the Pulse 2 into the presets, replacing them? It takes under a minute; slots "
                 "that do not answer become INIT. Nothing on the Pulse 2 changes.", "Backup", on_backup_confirmed);
}

void p2_draw_cancel_backup(void) {
    if ((gHost != NULL) && (gUser != NULL)) {
        gHost->cancelBackup(gUser);
    }
}

void p2_draw_backup_done(int found, bool stored) {
    char message[1200];

    if (found == 0) {
        show_alert("Backup Pulse 2 to Presets", "Cancelled. The presets are as they were.");
    } else if (!stored) {
        snprintf(message, sizeof(message), "Read %d sounds, but could not write %s.", found, p2_presets_path());
        show_alert("Backup Pulse 2 to Presets", message);
    } else {
        snprintf(message, sizeof(message), "Read %d sounds into the presets; %d slots did not answer and are INIT.", found,
                 P2_PATCH_SLOTS - found);
        show_alert("Backup Pulse 2 to Presets", message);
    }
}

// As SynthEdit's "Backing Up Bank": a box over the panel, the count and a bar
static void draw_backup_progress(void) {
    double boxW = 360.0, boxH = 90.0, margin = 10.0, titleH = 24.0;
    double boxX = (P2_CANVAS_W - boxW) / 2.0, boxY = (P2_CANVAS_H - boxH) / 2.0;
    double barW = boxW - (margin * 2.0), barY = boxY + boxH - margin - 8.0;
    char   line[96];

    if (!gBackupRunning) {
        return;
    }
    set_rgb_colour((tRgb)RGB_GREY_5);
    render_rectangle_with_border(mainArea, (tRectangle){{boxX, boxY}, {boxW, boxH}});
    set_rgb_colour((tRgb)RGB_GREY_3);
    render_rectangle(mainArea, (tRectangle){{boxX, boxY}, {boxW, titleH}});
    set_rgb_colour((tRgb)RGB_BLACK);
    render_text(mainArea, (tRectangle){{boxX + margin, boxY + 6.0}, {0.0, 13.0}}, "Backing Up Pulse 2");
    set_rgb_colour((tRgb)RGB_WHITE);
    snprintf(line, sizeof(line), "Sound %d of %d", gBackupAsked, P2_PATCH_SLOTS);
    render_text(mainArea, (tRectangle){{boxX + margin, boxY + titleH + margin}, {0.0, 13.0}}, line);
    snprintf(line, sizeof(line), "%d read so far (Pulse 2 > Cancel Backup to stop)", gBackupFound);
    render_text(mainArea, (tRectangle){{boxX + margin, boxY + titleH + margin + 19.0}, {0.0, 13.0}}, line);
    set_rgb_colour((tRgb)RGB_GREY_2);
    render_rectangle(mainArea, (tRectangle){{boxX + margin, barY}, {barW, 8.0}});
    set_rgb_colour((tRgb)RGB_GREEN_ON);
    render_rectangle(mainArea, (tRectangle){{boxX + margin, barY}, {barW * gBackupAsked / P2_PATCH_SLOTS, 8.0}});
}

// ---- import and export - notes §10 ------------------------------------------------------------------------

static uint8_t gImport[P2_PATCH_SLOTS][P2_DUMP_LENGTH];

static void on_import_confirmed(bool confirmed) {
    char failed[1200];

    if (!confirmed) {
        return;
    }

    if (!p2_presets_store_all(gImport)) {
        snprintf(failed, sizeof(failed), "Could not write %s", p2_presets_path());
        show_alert("Import Presets", failed);
    }
}

static void confirm_import(int count, const char * from) {
    static char message[1400];

    if (count == 0) {
        snprintf(message, sizeof(message), "No Pulse 2 sounds found in %s", from);
        show_alert("Import Presets", message);
        return;
    }
    snprintf(message, sizeof(message), "Replace all 500 presets with the %d sound%s in %s? Slots it has no sound for become INIT.",
             count, (count == 1) ? "" : "s", from);
    show_confirm("Import Presets", message, "Replace", on_import_confirmed);
}

static void on_import_file_chosen(const char * path) {
    if ((path != NULL) && (path[0] != '\0')) {
        confirm_import(p2_presets_read_file(path, gImport), path);
    }
}

static void on_import_folder_chosen(const char * path) {
    if ((path != NULL) && (path[0] != '\0')) {
        confirm_import(p2_presets_read_folder(path, gImport), path);
    }
}

static void on_export_file_chosen(const char * path) {
    char message[1200];

    if ((path == NULL) || (path[0] == '\0')) {
        return;
    }

    if (!p2_presets_write_file(path)) {
        snprintf(message, sizeof(message), "Could not write %s", path);
        show_alert("Export Presets", message);
    }
}

static void on_export_folder_chosen(const char * path) {
    char message[1200];
    int  written;

    if ((path == NULL) || (path[0] == '\0')) {
        return;
    }
    written = p2_presets_write_folder(path);

    if (written < P2_PATCH_SLOTS) {
        snprintf(message, sizeof(message), "Wrote %d of 500 files to %s", written, path);
        show_alert("Export Presets", message);
    }
}

void p2_draw_import_presets(bool folder) {
    set_file_browser_start_directory_provider(browser_start);

    if (folder) {
        open_file_browser_folder(on_import_folder_chosen, "Import Presets from Folder");
    } else {
        open_file_browser_read(on_import_file_chosen);
    }
}

void p2_draw_export_presets(bool folder) {
    set_file_browser_start_directory_provider(browser_start);

    if (folder) {
        open_file_browser_folder(on_export_folder_chosen, "Export Presets to Folder");
    } else {
        open_file_browser_write(on_export_file_chosen, "Pulse2Alike Presets.syx");
    }
}

static void on_revert_confirmed(bool confirmed) {
    if (confirmed) {
        load_preset(gPreset);
    }
}

void p2_draw_revert_preset(void) {
    static char message[160];

    if (gPreset == 0) {
        return;
    }
    snprintf(message, sizeof(message), "Discard the edits and go back to P%03d \"%s\"?", gPreset, p2_presets_name(gPreset));
    show_confirm("Revert to Stored Preset", message, "Revert", on_revert_confirmed);
}

bool p2_draw_has_patch_file(void) {
    return strchr(gPatchPath, '/') != NULL;
}

static void save_to(const char * path) {
    char failed[1400];

    if ((gHost != NULL) && gHost->save(gUser, path)) {
        p2_draw_set_patch(path);
        return;
    }
    snprintf(failed, sizeof(failed), "Could not write %s", path);
    show_alert("Save Patch", failed);
}

static void on_save_chosen(const char * path) {
    char   full[1100];
    size_t n;

    if ((path == NULL) || (path[0] == '\0')) {
        return;
    }
    snprintf(full, sizeof(full), "%s", path);
    n = strlen(full);

    if (((n < 4) || (strcmp(full + n - 4, ".syx") != 0)) && (n + 4 < sizeof(full))) {
        strcat(full, ".syx");
    }
    save_to(full);
}

static void on_overwrite_confirmed(bool confirmed) {
    if (confirmed) {
        save_to(gPatchPath);
    }
}

void p2_draw_save_patch(bool chooseFile) {
    static char  message[1200];
    const char * base = strrchr(gPatchPath, '/');

    if (!chooseFile && (base != NULL)) {
        snprintf(message, sizeof(message), "Overwrite \"%s\" with the sound as it is now?", base + 1);
        show_confirm("Save Patch", message, "Save", on_overwrite_confirmed);
        return;
    }
    // the suggestion: the current file's number, if it has one, and the sound's name
    {
        static char  suggested[64];
        const char * name   = ((gHost != NULL) && (gUser != NULL) && (gHost->name(gUser)[0] != '\0')) ? gHost->name(gUser) : "Untitled";
        int          number = (base != NULL) ? atoi(base + 1) : 0;

        if ((number > 0) && isdigit((unsigned char)base[1])) {
            snprintf(suggested, sizeof(suggested), "%03d %s.syx", number, name);
        } else {
            snprintf(suggested, sizeof(suggested), "%s.syx", name);
        }
        set_file_browser_start_directory_provider(browser_start);
        open_file_browser_write(on_save_chosen, suggested);
    }
}

static void on_init_confirmed(bool confirmed) {
    if (confirmed && (gHost != NULL)) {
        gHost->init(gUser);
        p2_draw_set_patch("Init");
    }
}

void p2_draw_send_to_hardware(void) {
    if ((gHost != NULL) && (gHost->send != NULL) && (gUser != NULL)) {
        int result = gHost->send(gUser);

        if (result != eP2HardwareSent) {
            p2_draw_hardware_problem(result);
        }
    }
}

void p2_draw_set_link_busy(bool busy) {
    gLinkBusy = busy;
}

void p2_draw_hardware_problem(int result) {
    show_alert("Pulse 2", (result == eP2HardwareNotFound) ? "No MIDI port with \"Pulse\" in its name. Is the Pulse 2 connected by USB?"
               : (result == eP2HardwareBusy) ? "Another Pulse2Alike has the Pulse 2 (its Link is on). Turn that off first."
               : "CoreMIDI would not send to the Pulse 2.");
}

void p2_draw_init_patch(void) {
    show_confirm("Init Patch", "Set every sound parameter to its default? No file is changed.", "Init", on_init_confirmed);
}

double p2_draw_value(uint32_t paramId) {
    return (paramId < MAX_PARAMS) ? gValue[paramId] : 0.0;
}

void p2_draw_edit(uint32_t paramId, double normalized) {
    if ((paramId < MAX_PARAMS) && (gHost != NULL)) {
        gValue[paramId] = normalized;
        gHost->edit(gUser, paramId, normalized);
    }
}

// ---- the name field - notes §6 ------------------------------------------------------------------------------

static void draw_name_field(void) {
    const char * shown = gNameEdit.active ? gNameEdit.buffer : (((gHost != NULL) && (gUser != NULL)) ? gHost->name(gUser) : "");

    gNameRect = (tRectangle){{
                                 PATCH_BAR_X + 182.0, TITLE_Y + 1.0
                             }, {
                                 NAME_FIELD_W, PATCH_BUTTON_H + 2.0
                             }
    };
    set_rgb_colour(gNameEdit.active ? (tRgb)RGB_GREY_3 : (tRgb)RGB_BACKGROUND_GREY);
    render_rectangle_with_border(mainArea, gNameRect);
    set_rgb_colour((tRgb)RGB_WHITE);
    render_text(mainArea, (tRectangle){{gNameRect.coord.x + 4.0, TITLE_Y + 3.0}, {0.0, 13.0}}, shown);

    if (gNameEdit.active) {
        char   before[P2_SOUND_NAME_LENGTH + 1];
        double x;

        snprintf(before, sizeof(before), "%.*s", (int)gNameEdit.cursor, gNameEdit.buffer);
        x = gNameRect.coord.x + 4.0 + get_text_width(before, 13.0, eNoCache);
        set_rgb_colour((tRgb)RGB_GREEN_ON);
        render_line(mainArea, (tCoord){x, TITLE_Y + 3.0}, (tCoord){x, TITLE_Y + 16.0}, 1.0);
    }
}

static void name_edit_begin(void) {
    snprintf(gNameEdit.buffer, sizeof(gNameEdit.buffer), "%s", ((gHost != NULL) && (gUser != NULL)) ? gHost->name(gUser) : "");
    gNameEdit.cursor = (uint32_t)strlen(gNameEdit.buffer);
    gNameEdit.active = true;
}

static void name_edit_commit(void) {
    gNameEdit.active = false;

    if ((gHost != NULL) && (gUser != NULL)) {
        gHost->rename(gUser, gNameEdit.buffer);
    }
}

// Return keeps it, Escape drops it; the instrument's names are capitals, so typing is too
static bool name_edit_key(int glfwKey, unsigned int codepoint) {
    size_t len = strlen(gNameEdit.buffer);

    switch (glfwKey) {
        case GLFW_KEY_ENTER:
        case GLFW_KEY_KP_ENTER: name_edit_commit();
            return true;

        case GLFW_KEY_ESCAPE: gNameEdit.active = false;
            return true;

        case GLFW_KEY_LEFT: gNameEdit.cursor  -= (gNameEdit.cursor > 0) ? 1 : 0;
            return true;

        case GLFW_KEY_RIGHT: gNameEdit.cursor += (gNameEdit.cursor < len) ? 1 : 0;
            return true;

        case GLFW_KEY_HOME: gNameEdit.cursor   = 0;
            return true;

        case GLFW_KEY_END: gNameEdit.cursor    = (uint32_t)len;
            return true;

        case GLFW_KEY_BACKSPACE:

            if (gNameEdit.cursor > 0) {
                memmove(&gNameEdit.buffer[gNameEdit.cursor - 1], &gNameEdit.buffer[gNameEdit.cursor], len - gNameEdit.cursor + 1);
                gNameEdit.cursor--;
            }
            return true;

        case GLFW_KEY_DELETE:

            if (gNameEdit.cursor < len) {
                memmove(&gNameEdit.buffer[gNameEdit.cursor], &gNameEdit.buffer[gNameEdit.cursor + 1], len - gNameEdit.cursor);
            }
            return true;

        default:
            break;
    }

    if ((glfwKey != GLFW_KEY_UNKNOWN) || (codepoint < 0x20u) || (codepoint > 0x7Eu) || (len >= P2_SOUND_NAME_LENGTH)) {
        return glfwKey != GLFW_KEY_UNKNOWN;   // an editing key with no meaning here is still the field's
    }
    memmove(&gNameEdit.buffer[gNameEdit.cursor + 1], &gNameEdit.buffer[gNameEdit.cursor], len - gNameEdit.cursor + 1);
    gNameEdit.buffer[gNameEdit.cursor++] = (char)toupper((int)codepoint);
    return true;
}

// ---- the arpeggiator's steps, on the ARP page - notes §7 ------------------------------------------------------

#define ARP_STEPS      (16)
#define STEPS_Y        (210.0)
#define STEP_ROW_H     (17.0)
#define STEP_CELL_H    (14.0)

static const char *const kStepEvents[] = {"OFF", "SOFT", "NORM", "HARD", "EVEN", "ODD", "OCT+", "1ST", "RESET"};
static const char *const kStepTimes[]  = {"25%", "50%", "75%", "100%"};
static tRectangle        gStepCell[ARP_STEPS][3];       // event, time, glide
static int               gStepMenuStep = -1, gStepMenuField = -1;

static bool arp_page(void) {
    return (gPageCount > 0) && (strcmp(gPages[gPage].title, "ARP") == 0);
}

static int step_byte(int i) {
    long v = lround(gValue[kP2ParamArpStep1 + (uint32_t)i] * 127.0);

    return (int)((v < 0) ? 0 : ((v > 127) ? 127 : v));
}

static void fitted_button(tRectangle r, const char * text, tRgb colour);

static void draw_steps(void) {
    int    length = (int)lround(gValue[kP2ParamArpLength] * 15.0) + 1;
    double w      = (P2_CANVAS_W - (2.0 * MARGIN_X)) / ARP_STEPS;
    char   number[8];

    set_rgb_colour((tRgb)RGB_WHITE);
    render_text(mainArea, (tRectangle){{MARGIN_X, STEPS_Y}, {0.0, 12.0}}, "STEPS");
    set_rgb_colour((tRgb)RGB_GREY_5);
    render_line(mainArea, (tCoord){MARGIN_X, STEPS_Y + 15.0}, (tCoord){P2_CANVAS_W - MARGIN_X, STEPS_Y + 15.0}, 1.0);

    for (int i = 0; i < ARP_STEPS; i++) {
        int    b      = step_byte(i);
        int    event  = ((b & 0x0F) > 8) ? 8 : (b & 0x0F);
        double x      = MARGIN_X + (i * w);
        tRgb   colour = (i < length) ? (tRgb){
            0.65, 0.65, 0.65
        }
                                                                : (tRgb)RGB_GREY_5;

        snprintf(number, sizeof(number), "%d", i + 1);
        set_rgb_colour((i < length) ? (tRgb)RGB_GREY_7 : (tRgb)RGB_GREY_5);
        render_text(mainArea, (tRectangle){{x, STEPS_Y + 20.0}, {0.0, LABEL_H}}, number);

        for (int f = 0; f < 3; f++) {
            gStepCell[i][f] = (tRectangle){{
                                               x, STEPS_Y + 34.0 + (f * STEP_ROW_H)
                                           }, {
                                               w - 3.0, STEP_CELL_H
                                           }
            };
        }

        fitted_button(gStepCell[i][0], kStepEvents[event], colour);
        fitted_button(gStepCell[i][1], kStepTimes[(b >> 4) & 3], colour);
        fitted_button(gStepCell[i][2], (b & 0x40) ? "GLIDE" : "-", ((b & 0x40) && (i < length)) ? (tRgb)RGB_GREEN_ON : colour);
    }
}

static void step_edit(int i, int b, tP2Edit * edit) {
    edit->paramId                          = kP2ParamArpStep1 + (uint32_t)i;
    edit->normalized                       = b / 127.0;
    gValue[kP2ParamArpStep1 + (uint32_t)i] = edit->normalized;
}

// A press on a step: Event and Time open their lists, Glide toggles at once
static bool step_press(double x, double y, tP2Edit * edit) {
    for (int i = 0; i < ARP_STEPS; i++) {
        for (int f = 0; f < 3; f++) {
            if (!within_rectangle((tCoord){x, y}, draw_button_bounds(gStepCell[i][f]))) {
                continue;
            }

            if (f == 2) {
                step_edit(i, step_byte(i) ^ 0x40, edit);
                return true;
            }
            int count = (f == 0) ? 9 : 4;

            for (int k = 0; k < count; k++) {
                gMenuItems[k] = (tMenuItem){
                    .label = (f == 0) ? kStepEvents[k] : kStepTimes[k], .colour = (tRgb)MENU_BG, .action = menu_action, .param = (uint32_t)k
                };
            }

            gMenuItems[count] = (tMenuItem){
                .label = NULL, .action = NULL
            };
            gMenuFor          = NULL;
            gMenuChoice       = -1;
            gStepMenuStep     = i;
            gStepMenuField    = f;
            open_context_menu(below_rect(gStepCell[i][f]), gMenuItems, 1, 0.0);
            return true;
        }
    }

    return false;
}

// A button whose label is shrunk to fit it (a mod target's name is wider than its box)
#define LABEL_MIN_H    (7.0)

static void fitted_button(tRectangle r, const char * text, tRgb colour) {
    double h = r.size.h;

    while ((h > LABEL_MIN_H) && (get_text_width(text, h, eNoCache) > r.size.w)) {
        h -= 0.5;
    }
    // where draw_button puts its own label: the box grows by its margin all round, the text starts a margin in
    draw_button(mainArea, r, "", colour);
    set_rgb_colour((tRgb)RGB_BLACK);
    render_text(mainArea, (tRectangle){{r.coord.x + DRAW_BUTTON_MARGIN, r.coord.y + DRAW_BUTTON_MARGIN + ((r.size.h - h) / 2.0)}, {0.0, h}}, text);
}

static int32_t step_of(const tP2Control * c) {
    long step = lround(gValue[c->paramId] * c->steps);

    return (int32_t)((step < 0) ? 0 : ((step > c->steps) ? c->steps : step));
}

// notes §3: sections flow left to right and wrap onto a new row when the next would not fit
static void layout(void) {
    gPlacedCount        = 0;
    gPlacedSectionCount = 0;

    if ((gPages == NULL) || (gPage >= gPageCount)) {
        return;
    }
    const tP2Page * page = &gPages[gPage];
    double          x    = MARGIN_X;
    double          y    = PAGE_Y;

    for (uint32_t s = 0; (s < page->count) && (gPlacedSectionCount < MAX_PLACED); s++) {
        const tP2Section * section = &page->sections[s];
        double             w       = section->count * CONTROL_W;

        if ((x > MARGIN_X) && ((x + w) > (P2_CANVAS_W - MARGIN_X))) {
            x  = MARGIN_X;
            y += ROW_H;
        }
        gPlacedSections[gPlacedSectionCount++] = (tPlacedSection){
            section, x, y, w
        };

        for (uint32_t i = 0; (i < section->count) && (gPlacedCount < MAX_PLACED); i++) {
            double cx = x + (i * CONTROL_W);

            gPlaced[gPlacedCount++] = (tPlaced){
                &section->controls[i], section,
                {{
                     cx + ((CONTROL_W - DIAL_SIZE) / 2.0), y + HEADING_TO_DIAL
                 }, {
                     DIAL_SIZE, DIAL_SIZE
                 }
                },
                cx
            };
        }

        x                                     += w + SECTION_GAP;
    }
}

static void value_text(const tP2Control * c, char * out, size_t len) {
    int32_t step = step_of(c);

    if (c->names != NULL) {
        snprintf(out, len, "%s", c->names[step]);
    } else {
        snprintf(out, len, "%d", (int)lround(c->plainMin + step));
    }
}

static void draw_tabs(void) {
    double x = MARGIN_X;

    for (uint32_t p = 0; p < gPageCount; p++) {
        double w = get_text_width(gPages[p].title, TAB_H - 2.0, eNoCache) + 12.0;

        gTabs[p] = (tRectangle){{
                                    x, TAB_Y
                                }, {
                                    w, TAB_H
                                }
        };
        draw_button(mainArea, gTabs[p], gPages[p].title, (p == gPage) ? (tRgb)RGB_GREEN_ON : (tRgb)RGB_GREY_7);
        x       += w + TAB_GAP;
    }
}

void p2_draw_frame(int pixelWidth, int pixelHeight) {
    char text[64];

    if ((pixelWidth <= 0) || (pixelHeight <= 0)) {
        return;
    }
    render_backend_set_surface(pixelWidth, pixelHeight);
    set_render_width(pixelWidth);
    set_render_height(pixelHeight);
    gGlobalGuiScale = (double)pixelWidth / P2_CANVAS_W;
    render_backend_clear((tRgb)RGB_BACKGROUND_GREY);

    if (!gFontReady) {
        render_backend_flush();
        return;
    }
    set_rgb_colour((tRgb){0.95, 0.95, 0.97});
    render_text(mainArea, (tRectangle){{MARGIN_X, TITLE_Y}, {0.0, 18.0}}, "Pulse2Alike");
    draw_tabs();
    layout();
    {
        char         name[160];
        const char * base = strrchr(gPatchPath, '/');

        gPrevRect = (tRectangle){{
                                     PATCH_BAR_X, TITLE_Y + 2.0
                                 }, {
                                     52.0, PATCH_BUTTON_H
                                 }
        };
        gNextRect = (tRectangle){{
                                     PATCH_BAR_X + 58.0, TITLE_Y + 2.0
                                 }, {
                                     52.0, PATCH_BUTTON_H
                                 }
        };
        gLoadRect = (tRectangle){{
                                     PATCH_BAR_X + 116.0, TITLE_Y + 2.0
                                 }, {
                                     56.0, PATCH_BUTTON_H
                                 }
        };
        gLinkRect = (tRectangle){{
                                     PATCH_BAR_X - 72.0, TITLE_Y + 2.0
                                 }, {
                                     62.0, PATCH_BUTTON_H
                                 }
        };
        // notes §8: lit while the instrument follows the sound
        // notes §8: amber and "Link busy" while another instance has the instrument
        draw_button(mainArea, gLinkRect, gLinkBusy ? "Link busy" : "Link HW",
                    (p2_draw_value(kP2ParamHwLink) < 0.5) ? (tRgb)RGB_GREY_7 : (gLinkBusy ? (tRgb){0.85, 0.6, 0.15}
                                                                                                                    : (tRgb)RGB_GREEN_ON));
        draw_button(mainArea, gPrevRect, "< Prev", (tRgb)RGB_GREY_7);
        draw_button(mainArea, gNextRect, "Next >", (tRgb)RGB_GREY_7);
        draw_button(mainArea, gLoadRect, "Load...", (tRgb)RGB_GREY_7);
        draw_name_field();

        if (gPreset > 0) {
            snprintf(name, sizeof(name), "P%03d%s", gPreset, gPresetEdited ? "*" : "");
            set_rgb_colour(gPresetEdited ? (tRgb)RGB_WHITE : (tRgb)RGB_GREY_5);
            render_text(mainArea, (tRectangle){{gNameRect.coord.x + gNameRect.size.w + 8.0, TITLE_Y + 4.0}, {0.0, 11.0}}, name);
        } else if (base != NULL) {
            snprintf(name, sizeof(name), "%s", base + 1);

            if ((strlen(name) > 4) && (strcmp(name + strlen(name) - 4, ".syx") == 0)) {
                name[strlen(name) - 4] = '\0';
            }

            if (strlen(name) > FILE_LABEL_CHARS) {
                name[FILE_LABEL_CHARS] = '\0';
            }
            set_rgb_colour((tRgb)RGB_GREY_5);
            render_text(mainArea, (tRectangle){{gNameRect.coord.x + gNameRect.size.w + 8.0, TITLE_Y + 4.0}, {0.0, 11.0}}, name);
        }
    }

    for (uint32_t s = 0; s < gPlacedSectionCount; s++) {
        tPlacedSection * ps = &gPlacedSections[s];

        set_rgb_colour((tRgb)RGB_WHITE);
        render_text(mainArea, (tRectangle){{ps->x, ps->y}, {0.0, 12.0}}, ps->section->title);
        set_rgb_colour((tRgb)RGB_GREY_5);
        render_line(mainArea, (tCoord){ps->x, ps->y + 15.0}, (tCoord){ps->x + ps->w - 6.0, ps->y + 15.0}, 1.0);
    }

    for (uint32_t i = 0; i < gPlacedCount; i++) {
        tPlaced *          pc     = &gPlaced[i];
        const tP2Control * c      = pc->control;
        tRgb               colour = {pc->section->colour[0], pc->section->colour[1], pc->section->colour[2]};

        set_rgb_colour((tRgb)RGB_GREY_7);
        render_text(mainArea, (tRectangle){{pc->x, pc->dial.coord.y - 14.0}, {0.0, LABEL_H}}, c->label);
        value_text(c, text, sizeof(text));

        if (c->kind == eP2ControlChoice) {
            fitted_button((tRectangle){{pc->x, pc->dial.coord.y + ((DIAL_SIZE - BUTTON_H) / 2.0)}, {CONTROL_W - 6.0, BUTTON_H}}, text, colour);
        } else {
            render_dial(mainArea, pc->dial, (uint32_t)step_of(c), (uint32_t)c->steps, 0, colour);
            set_rgb_colour((tRgb)RGB_WHITE);
            render_text(mainArea, (tRectangle){{pc->x, pc->dial.coord.y + DIAL_SIZE + 6.0}, {0.0, LABEL_H}}, text);
        }
    }

    if (arp_page()) {
        draw_steps();
    }
    render_menu_bar(p2_menu_bar(), p2_menu_bar_rect());
    synthlib_popups_tick();
    draw_backup_progress();
    synthlib_popups_render();  // menus, the file browser and dialogues, front-most last
    render_backend_flush();
}

static const tPlaced * hit(double x, double y) {
    for (uint32_t i = 0; i < gPlacedCount; i++) {
        tPlaced * pc = &gPlaced[i];

        if ((x >= pc->x) && (x < pc->x + CONTROL_W) && (y >= pc->dial.coord.y - 16.0) && (y < pc->dial.coord.y + DIAL_SIZE + 20.0)) {
            return pc;
        }
    }

    return NULL;
}

static void open_value_menu(const tPlaced * pc) {
    const tP2Control * c       = pc->control;
    int                count   = (c->steps + 1 < MENU_MAX) ? (c->steps + 1) : MENU_MAX;
    uint32_t           columns = (uint32_t)((count + MENU_ROWS_PER_COLUMN - 1) / MENU_ROWS_PER_COLUMN);

    for (int i = 0; i < count; i++) {
        gMenuItems[i] = (tMenuItem){
            .label = c->names[i], .colour = (tRgb)MENU_BG, .action = menu_action, .param = (uint32_t)i
        };
    }

    gMenuItems[count] = (tMenuItem){
        .label = NULL, .action = NULL
    };
    gMenuFor          = c;
    gMenuChoice       = -1;
    open_context_menu(below_rect(pc->dial), gMenuItems, columns, MENU_CELL_W);
}

// notes §1
bool p2_draw_press(double x, double y, tP2Edit * edit, bool * grabbed) {
    *grabbed      = false;
    edit->paramId = UINT32_MAX;

    // notes §5: the popups first, front to back - a dialogue or the file browser takes every press, a menu the
    // presses on it, the menu bar its own; a press anywhere else while a menu is open only closes it
    if (synthlib_popups_dispatch_click((tCoord){x, y}, mouseButtonLeftDown)) {
        return true;
    }

    if (gContextMenu.active) {
        close_context_menu();
        gMenuFor = NULL;
        return true;
    }

    // notes §6: a press on the name edits it; anywhere else while editing keeps the edit, then acts as usual
    if (within_rectangle((tCoord){x, y}, gNameRect)) {
        if (!gNameEdit.active) {
            name_edit_begin();
        }
        return true;
    }

    if (gNameEdit.active) {
        name_edit_commit();
    }

    if (within_rectangle((tCoord){x, y}, draw_button_bounds(gLinkRect))) {
        edit->paramId    = kP2ParamHwLink;
        edit->normalized = (p2_draw_value(kP2ParamHwLink) >= 0.5) ? 0.0 : 1.0;
        return true;
    }

    if (within_rectangle((tCoord){x, y}, draw_button_bounds(gPrevRect))) {
        step_patch(-1);
        return true;
    }

    if (within_rectangle((tCoord){x, y}, draw_button_bounds(gNextRect))) {
        step_patch(1);
        return true;
    }

    if (within_rectangle((tCoord){x, y}, draw_button_bounds(gLoadRect))) {
        p2_draw_open_patch();
        return true;
    }

    for (uint32_t p = 0; p < gPageCount; p++) {
        if (within_rectangle((tCoord){x, y}, draw_button_bounds(gTabs[p]))) {
            gPage = p;
            return true;
        }
    }

    if (arp_page() && step_press(x, y, edit)) {
        return true;
    }
    layout();
    const tPlaced * pc = hit(x, y);

    if (pc == NULL) {
        return false;
    }

    if (pc->control->kind == eP2ControlChoice) {
        open_value_menu(pc);
        return true;
    }
    gGrabbed   = pc->control;
    gGrabValue = gValue[pc->control->paramId];
    gGrabDial  = pc->dial;
    *grabbed   = true;
    return true;
}

bool p2_draw_drag_by(double dx, double dy, tP2Edit * edit) {
    // up or right raises it, as the Controls menu chose
    double move = (p2_dial_mode() == eDialModeHorizontal) ? dx : -dy;

    if (gGrabbed == NULL) {
        return false;
    }
    gGrabValue                = fmin(1.0, fmax(0.0, gGrabValue + (move / dial_drag_pixels_for_full_range((uint32_t)gGrabbed->steps))));
    edit->paramId             = gGrabbed->paramId;
    edit->normalized          = gGrabValue;
    gValue[gGrabbed->paramId] = gGrabValue;
    return true;
}

// notes §9: Rotary - the pointer stays, and the dial takes its angle
bool p2_draw_drag_to(double x, double y, tP2Edit * edit) {
    if ((gGrabbed == NULL) || (gGrabbed->steps <= 0)) {
        return false;
    }
    uint32_t range = (uint32_t)gGrabbed->steps + 1;

    gGrabValue                = (double)angle_to_value(calculate_mouse_angle((tCoord){x, y}, gGrabDial), range) / (double)gGrabbed->steps;
    edit->paramId             = gGrabbed->paramId;
    edit->normalized          = gGrabValue;
    gValue[gGrabbed->paramId] = gGrabValue;
    return true;
}

// A release ends a drag, and is where a menu's choice is taken (the press opened it, the release on an item picks)
void p2_draw_release(double x, double y, tP2Edit * edit) {
    edit->paramId = UINT32_MAX;
    gGrabbed      = NULL;
    gMenuChoice   = -1;

    if (synthlib_popups_dispatch_click((tCoord){x, y}, mouseButtonLeftUp) && (gMenuChoice >= 0) && (gMenuFor != NULL)) {
        edit->paramId             = gMenuFor->paramId;
        edit->normalized          = (double)gMenuChoice / gMenuFor->steps;
        gValue[gMenuFor->paramId] = edit->normalized;
    } else if ((gStepMenuStep >= 0) && (gMenuChoice >= 0)) {
        int b = step_byte(gStepMenuStep);

        b             = (gStepMenuField == 0) ? ((b & ~0x0F) | gMenuChoice) : ((b & ~0x30) | (gMenuChoice << 4));
        step_edit(gStepMenuStep, b, edit);
        gStepMenuStep = -1;
    }

    if (!gContextMenu.active) {
        gStepMenuStep = -1;
    }

    if (!gContextMenu.active) {
        gMenuFor = NULL;
    }
}

void p2_draw_scroll(double dy) {
    // the browsers count rows, the wheel logical units
    if (!synthlib_popups_dispatch_scroll(-dy / 20.0) && gContextMenu.active) {
        context_menu_scroll(dy / 20.0);
    }
}

bool p2_draw_key(int glfwKey, unsigned int codepoint, bool isRepeat) {
    int action = isRepeat ? GLFW_REPEAT : GLFW_PRESS;

    if (gNameEdit.active && !synthlib_popups_modal_active()) {
        return name_edit_key(glfwKey, codepoint);
    }

    if ((glfwKey == GLFW_KEY_ESCAPE) && gContextMenu.active && !synthlib_popups_modal_active()) {
        close_context_menu();
        gMenuFor = NULL;
        return true;
    }

    if (glfwKey != GLFW_KEY_UNKNOWN) {
        return synthlib_popups_dispatch_key(glfwKey, 0, action);
    }
    return (codepoint >= 0x20u) && (codepoint != 0x7Fu) && synthlib_popups_dispatch_char(codepoint);
}
