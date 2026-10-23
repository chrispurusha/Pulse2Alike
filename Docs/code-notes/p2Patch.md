# p2Patch.c / p2Patch.h - notes

## 1. The sound dump
`F0 3E 16 <dev> 10 <bank> <prog> <128 sound bytes> <checksum> F7`, 137 bytes. The sound bytes are the instrument's
parameters in its own order (`gP2SoundBytes` maps each onto a plug-in parameter). Bytes 113-126 are the name.

## 2. The presets
P001-P500 live in one file, `~/Library/Application Support/Pulse2Alike/presets.syx` beside the prefs (design §7):
500 sound dumps back to back, slot n at byte (n - 1) x 137, so the file is itself a valid multi-message `.syx`.
It is read once per process into a cache that a program change reads, so a program change does no file access.
Every slot always holds a sound: one the file does not have (no file, a short one, or bytes that are not a sound
dump) is INIT, as an empty slot on the instrument is. Reading never writes the file; the first store creates it.
Single sounds still come and go as their own `.syx` files (File menu); `p2_patch_sounds_folder()` is only where the
file browser starts.

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

## 6. The presets file, written through
A slot's dump is addressed to it: bytes 5-6 are (n - 1) as two 7-bit bytes, as the instrument numbers a slot in
its own dumps (P206 is `01 4D`, P500 is `03 73`), checksum recomputed. A store puts the dump in the cache and then
rewrites that slot's 137 bytes in place in the file (`pwrite`); if the file is missing or not 68,500 bytes, the
whole cache is written instead, through a temporary file renamed over it, so a failed write never leaves half a
file. Every store and every read notes the file's modification time; `p2_presets_refresh()` re-reads the file when
that time has moved, which is how one instance sees another process's store. Within a process the cache is shared,
so every instance sees a store at once. INIT is every parameter at its default, named INIT, device byte 00.

## 7. Import and export
A `.syx` file of any length is read dump by dump: each goes to the slot it is addressed to, or, when it is
addressed to the edit buffer (`7F 00`), to the slot after the last one placed. Bytes that are not a sound dump are
skipped one at a time until one starts. A folder is read as `NNN Name.syx` files, NNN the slot - the format of the
instrument's backup in `iCloud Drive/Patches/Pulse2` and of an export. Either way the slots with no sound become
INIT, and nothing is stored until the panel's confirm. Exporting writes the 500 as one file, or as 500 `NNN Name.syx`
files with the name's trailing spaces dropped and `/` and `:` made `-`. Checked: the 407-sound library imported,
exported as a file and as a folder and re-imported, identical each way (2026-10-23).
