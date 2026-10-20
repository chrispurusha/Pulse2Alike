# p2Prefs.c - notes

## 1. The settings file
`~/Library/Application Support/Pulse2Alike/prefs.txt`, SynthLib's prefs, as G2 Alike's `g2Prefs.c` keeps its own.
It holds what belongs to the user and the rig rather than to a project: the drag direction (`dialMode`, Controls
menu; vertical unless horizontal was chosen) and the Pulse 2's MIDI channel (`pulse2Channel`, p2Plugin notes §46).
Read once per process when the first instance is created; each change is written when it is made.

## 2. The drag mode is the plug-in's own
SynthLib's plug-in stubs (`pluginStubs.c`) answer Rotary for `synthlib_dial_mode()` and ignore
`synthlib_set_dial_mode()`, because the plug-ins they were written for had no dials. Pulse2Alike went through them
until 2026-10-20, so its Controls menu changed nothing and every drag was vertical. It now keeps the mode here,
saved as `dialMode` with the sibling apps' values (0 rotary, 1 vertical, 2 horizontal); the default is vertical.
