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
