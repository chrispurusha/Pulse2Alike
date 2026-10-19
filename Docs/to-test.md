# To test

Built, not yet checked against the instrument or in a host. Confirmed → delete the line; failed → move it to `todo.md`.

- Pulse2Alike loads and plays in Live (VST3 and AU), last-note priority, no clicks at note on/off
- Osc 2 semitone offset against the instrument's osc 2 semitone at the same setting
- The panel opens in Live (VST3 and AU), dials turn by dragging up/down, Shape/Type buttons step, values follow host automation
- The filter by ear: LP24/LP12/BP12/HP12, resonance self-oscillating from 97 with a note held, silent with none
- Patch bar: Prev/Next step through iCloud Patches/Pulse2 in slot order; Load... opens the browser sized to the panel (rows fit 300 high), scrolls with wheel/trackpad, a chosen sound loads and every page follows
- Menus on the MOD page open as 4 short columns and do not overflow the bottom
- Program change in Live: AU (MIDI 0xC0) and VST3 (the kIsProgramChange parameter); bank select CC 32 first for P101+; the panel's patch name follows
- File menu in Live: Open, Load by Number, Save (confirm), Save As (type a name: needs the keyboard in Live's plug-in window), Init, Reload Library
- Rename: click the name, type, Return; Escape cancels; then Save writes the new name (load it back to check)
- Reopen a Live project: the name and file come back; Save still keeps the original dump's other bytes
- Controls > Drag Dials Horizontally; Anomalies toggle
- Drive TUBE and FUZZ by ear against the instrument; osc 3 routings LEVEL2 / VCF / DRIVE and the FB shape (depths are guesses)
- P004 at several notes against the plug-in (Keytrack OFF itself is confirmed)
- Program change to the current program is ignored (host re-sends it)
- Arpeggiator in Live, against the instrument: modes, Range, Clock, Step Duration, Swing, HOLD, following Live's tempo and bars; a step pattern with OFF/SOFT/HARD/EVEN/ODD/OCT+/1ST/RESET (P015 DOPPLER uses HOLD)
- P006 by ear again (osc 3 on LEVEL2 three times deeper, osc 3 louder: its tone now stands against the noise as the instrument's does)
