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
- Anomalies toggle
- Drive TUBE and FUZZ by ear against the instrument; osc 3 routings LEVEL2 / VCF / DRIVE and the FB shape (depths are guesses)
- P004 at several notes against the plug-in (Keytrack OFF itself is confirmed)
- Program change to the current program is ignored (host re-sends it)
- Arpeggiator in Live, against the instrument: modes, Range, Clock, Step Duration, Swing, HOLD, following Live's tempo and bars; a step pattern with OFF/SOFT/HARD/EVEN/ODD/OCT+/1ST/RESET (P015 DOPPLER uses HOLD)
- P006 by ear again (osc 3 on LEVEL2 three times deeper, osc 3 louder: its tone now stands against the noise as the instrument's does)
- Hiss switch (GLOBAL page): on, a dark patch (P009) should gain the instrument's faint top-end hiss; off by default
- Link button / File > Send Sound to Pulse 2: set Pulse 2 MIDI Channel (GLOBAL) to 12, Link on, turn knobs and load sounds; the instrument should follow. Mod matrix edits go as dumps (at most 10 a second)
- P004 with osc 1 down, C3/F3 alternating: osc 2 should step to each note about 0.2 s in, held or not; first note after loading without a thump
- P006: the noise should now sit as on the instrument (the filter's leak no longer gets the LEVEL2 routing gain)
- P006 osc 1 alone (osc 2, 3 down): the triangle should have the instrument's slightly pulse-like colour (per-oscillator asymmetry)
- Arp sounds to other sounds by program change: no note carried over or stuck (long Step Duration and Swing especially); OFF→arp with keys held hands them to the arp; HOLD→OFF→HOLD resumes the kept chord only with Anomalies on
- Controls > Rotary / Vertical / Horizontal: each drags as named (Rotary follows the angle round the dial with the pointer hidden); the choice and the Pulse 2 channel survive closing Live (~/Library/Application Support/Pulse2Alike/prefs.txt)
- Fault guard (p2Plugin notes §47): normal playing never logs FAULT in /tmp/pulse2alike.log; if Hiss (or anything) breaks the sound again, it should come back by itself within a block
