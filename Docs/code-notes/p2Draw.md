# p2Draw.c / p2Draw.h - notes

The editor panel, drawn through SynthLib's renderer with SynthEdit's look: dark grey, section headings with a
rule, `render_dial()` for continuous controls, and `draw_button()` for lists, which step on each click. It is
hosted by SynthLib's `synthlibPanelView`, as MidiSyncTool's and GenBridge's panels are.

## 1. Dragging a dial
As SynthEdit and G2Alike do it. A press on a dial grabs it, and SynthLib's panel view hides the pointer and
holds it still. The raw movement turns the dial, at `dial_drag_pixels_for_full_range()` per full range, which
is SynthLib's shared policy, so Shift drags slowly. On release the pointer reappears where it was. The value
runs unrounded while it moves, so a continuous parameter (cutoff, resonance) moves smoothly.

## 2. Value menus
A list control (the oscillator shapes, the filter type) opens SynthLib's context menu under itself, as
SynthEdit's value menus and MidiSyncTool's selectors do. While the menu is open, a click belongs to it, either
choosing or dismissing, never to the control underneath.

## 3. Pages and layout
Page tabs across the top (SynthEdit's `draw_button`, green for the current page), then the page's sections
flowing left to right and wrapping onto a new row when the next would not fit. Layout is recomputed every
frame and every press, from the page table alone, so a page needs no coordinates of its own. Value menus
open in columns of 8 rows (the 32 modulation targets as 4 columns), so a long list fits under a control in
the lower row instead of scrolling.

## 4. Presets: Prev, Next, the label
`< Prev` and `Next >` step through P001-P500 and wrap at both ends, as the instrument's own buttons do; from a sound
opened as a numbered file (`004 Name.syx`) they step from its number; from any other (Init, an unnumbered file)
Next goes to P001 and Prev to P500. `Load...` opens SynthLib's in-window file browser
for a single `.syx`, starting in the current file's folder or `iCloud Drive/Patches/Pulse2`. The browser is modal
and drawn last; while it is open every press, release, hover and scroll is its own.

After the name: the preset (`P012`, grey; `P012*`, white, once edited - p2Plugin notes §48), or the file's name
when the sound came from a file. Load Preset... and Store Preset to... choose the slot in SynthLib's bank browser,
as SynthEdit and G2Alike choose a bank location: 500 named rows as banks 1-5 of 100, sortable A-Z. A store is
always confirmed, naming what the slot holds now; so is Revert.

## 5. Menus and popups
The menu bar (p2Menu.c) sits across the top of the panel; everything else is 20 units lower. Menus, the file
browser and the dialogues all go through SynthLib's synthlibPopups, as in G2Alike's editor: a press is offered
to them front to back first, and a press anywhere else while a menu is open only closes it. A menu item is chosen
on the RELEASE (contextMenu acts on mouse-up), which is why p2_draw_release returns an edit: a list control's
value menu is chosen there too. Keys come from SynthLib's panel view once a click has given it the keyboard.

## 6. The name field
The sound's name, beside Prev/Next/Load, edited in place as SynthEdit edits a program name: a click starts it,
Return or a click elsewhere keeps it, Escape drops it. Typing is upper-cased and stops at 14 characters, which
is the dump's name field and how the instrument's own sounds are named. The name goes to a file only at the
next save. The file the sound came from is shown greyed after it.

## 7. The arpeggiator's steps
Below the ARP page's dials, the 16 steps, each three cells: its Event and Time (lists) and Glide (a toggle). A
step past Pattern Length is greyed. Each step is one parameter, the instrument's own byte (p2Arp notes §2), so
an edit changes only the bits it shows.

## 8. Link
The Link HW button, left of Prev, shows and flips the Link setting (p2Plugin notes §41) - green while on. The work is the
plug-in's, through the host's `send`; the panel only reports a failure. Amber, reading "Link busy", while Link is on
but another instance owns the instrument (p2Plugin notes §49).

## 9. Rotary drag
Controls offers Rotary, Vertical and Horizontal, as the sibling editors do. Vertical and Horizontal hide the
pointer and count its movement; Rotary keeps it visible and free, as the siblings' Rotary does, and the dial takes
the pointer's angle about its centre (SynthLib's `calculate_mouse_angle()` / `angle_to_value()`, the 270 degree
sweep the siblings use). The panel view asks at each grab which kind of drag it is (its `keepsPointer`, SynthLib
synthlibPanelView notes §12).

## 10. Import and export
Presets > Import from File/Folder reads the sounds (p2Patch notes §7) and asks before replacing all 500, saying how
many it found and that the rest become INIT; nothing is written unless confirmed. Export writes the 500 as they
are, and reports only a failure.

## 11. Backup progress
Pulse 2 > Backup Pulse 2 to Presets... asks first (all 500 replaced; nothing on the instrument changes), then shows
SynthEdit's "Backing Up Bank" box over the panel: the sound being asked for, how many have answered, a bar. The
menu offers Cancel Backup while it runs. The end says how many were read and how many are INIT.
