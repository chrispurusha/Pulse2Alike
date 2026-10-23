# p2Menu.c - notes

The panel's menu bar, modelled on SynthEdit's, with only the items that make sense without the instrument
connected (no Device, Backup or Restore; those talk to the hardware).

- **File:** Open Patch..., Load Patch by Number, Save Patch (over the current file, after a confirm; disabled with
  no file), Save Patch As... (suggests "NNN NAME.syx"), Init Patch..., Reload Patch Library (rescans the folder,
  for a backup made while the plug-in is open).
- **Controls:** dial drag direction (rotary is not offered yet: a drag hides and holds the pointer). Anomalies
  stays on the Global page only.
- **Help:** About.

## 1. Load Patch by Number
Three short levels (bank of 100, ten sounds, the sounds by name), so no level is wider or taller than the
panel. It is rebuilt each time the File menu opens, so a save or a reload shows straight away. A number with no
file in the library is greyed. The action reads the sound number from the item's param.

## 2. Help
Four topics, each one SynthLib alert (word-wrapped, at most 32 lines - a longer text is cut, not scrolled): the
panel, sounds and program changes, linking a Pulse 2, and the plug-in's own settings. They describe what the
plug-in does now; the sounds topic changes with the presets file (design §7).

## 3. Presets
Load Preset..., Store Preset to P012 (back to the one it came from), Store Preset to..., Revert to Stored P012, and
import and export of all 500 (p2Draw notes §4, §10). Store and Revert are greyed with no preset.

## 4. Pulse 2
What talks to the instrument: Send Sound to Pulse 2 (its edit buffer) and Backup Pulse 2 to Presets... - Cancel
Backup in its place while one runs. Nothing here writes the instrument's memory yet: Store Sound to Slot and
Restore Presets to Pulse 2 wait (CT, 2026-10-23).
