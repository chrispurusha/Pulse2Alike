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

#ifndef __P2_DRAW_H__
#define __P2_DRAW_H__

#include <stdbool.h>
#include <stdint.h>

#define P2_CANVAS_W    (780.0)
#define P2_CANVAS_H    (320.0)

typedef enum {
    eP2ControlDial = 0,
    eP2ControlChoice        // a button that steps through a list
} tP2ControlKind;

typedef struct {
    uint32_t            paramId;
    const char *        label;
    tP2ControlKind      kind;
    int32_t             steps;   // plain range is 0..steps for a dial, entries - 1 for a choice
    double              plainMin;
    const char *const * names;   // a choice's entries
} tP2Control;

typedef struct {
    const char *       title;
    double             colour[3];
    const tP2Control * controls;
    uint32_t           count;
} tP2Section;

typedef struct {
    const char *       title;
    const tP2Section * sections;
    uint32_t           count;
} tP2Page;

// What a click or drag asked for: one parameter, its new normalized value.
typedef struct {
    uint32_t paramId;
    double   normalized;
} tP2Edit;

void p2_draw_init(void);
void p2_draw_set_pages(const tP2Page * pages, uint32_t count);
void p2_draw_set_value(uint32_t paramId, double normalized);
void p2_draw_set_mouse(double x, double y);
void p2_draw_frame(int pixelWidth, int pixelHeight);
bool p2_draw_menu_active(void);

// A press: opens a list control's menu, takes a choice from an open one (edit->paramId is UINT32_MAX when
// nothing was set), or grabs a dial (*grabbed, and the pointer is then held while dragBy moves it).
bool p2_draw_press(double x, double y, tP2Edit * edit, bool * grabbed);
bool p2_draw_drag_by(double dx, double dy, tP2Edit * edit);
void p2_draw_release(double x, double y, tP2Edit * edit);   // a menu choice is taken here
bool p2_draw_key(int glfwKey, unsigned int codepoint, bool isRepeat);
void p2_draw_scroll(double dy);

// notes §4: patches, and what the menus do with them (notes §5). The host does the work on the sound.
typedef struct {
    void (*load)(void * user, const char * path);                 // a .syx chosen (Open, Prev/Next, by number)
    bool (*save)(void * user, const char * path);                 // the sound as it is now; false if not written
    void (*init)(void * user);                                    // every sound parameter to its default
    void (*edit)(void * user, uint32_t paramId, double normalized);
    const char * (*name)(void * user);                            // the sound's name, as shown
    void (*rename)(void * user, const char * name);               // notes §6: an edited name, on commit
    int (*send)(void * user);                                     // notes §8: to the instrument's edit buffer
} tP2PatchHost;

void p2_draw_set_host(const tP2PatchHost * host); // static storage
void p2_draw_set_user(void * user);
void p2_draw_set_patch(const char * path);        // what is loaded now, for the name and for Prev/Next; no '/' = a title

void p2_draw_open_patch(void);
void p2_draw_load_number(int number);
bool p2_draw_has_patch_file(void);
void p2_draw_save_patch(bool chooseFile);         // false: over the current file, after a confirm
void p2_draw_init_patch(void);
void p2_draw_send_to_hardware(void);
void p2_draw_hardware_problem(int result);   // a tP2HardwareResult that is not eP2HardwareSent
double p2_draw_value(uint32_t paramId);
void p2_draw_edit(uint32_t paramId, double normalized);

#endif // __P2_DRAW_H__
