# p2Patch.c / p2Patch.h - notes

## 1. The sound dump
`F0 3E 16 <dev> 10 <bank> <prog> <128 sound bytes> <checksum> F7`, 137 bytes. The sound bytes are the instrument's
parameters in its own order (`gP2SoundBytes` maps each onto a plug-in parameter). Bytes 113-126 are the name.

## 2. The cache
Every `NNN *.syx` in the patch folder (NNN = display number) is read once into memory, so a program change does
no file access. If the folder changes later (a new backup), the plug-in has to be reloaded to see it.

## 3. Program numbers
100 sounds to a bank: bank select mod 5, programs above 99 clamped (findings, "program change").

## 4. Writing a dump
p2_patch_to_syx is the inverse of p2_patch_from_syx. The bytes the plug-in models come from the parameters, and
the rest from the dump the sound was loaded from, so a save does not lose what the plug-in does not model. With
no such dump (after Init) the others are zero and the dump is addressed to the edit buffer (7F 00). Checked
against the library: 406 of 407 files write back byte for byte. P500 holds 119 in its first sound byte, out of
that parameter's range, and is written clamped.

## 5. The cache is a seqlock per slot
The main thread writes a slot (a save into the library, Reload Patch Library), and the audio thread reads it on
a program change. Each slot has a generation, odd while it is being written. The reader copies the dump and keeps
the copy only if the generation was even and unchanged: no lock, and no torn sound.
