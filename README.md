# Pulse2Alike

A reproduction inspired by the Waldorf Pulse 2 as a VST3 and Audio Unit instrument.

The analogue parts are modelled from captures of a real Pulse 2: the oscillator wave shapes, the
filter (LP24 / LP12 / BP12 / HP12), and the drive and VCA. Captures are taken through the instrument's
external input and MIDI control.

## Relationship to the sibling projects

One of a family that shares [SynthLib](https://github.com/chrispurusha/SynthLib) and its format-free
plug-in wrappers:

- **G2-Edit**: editor for the Nord G2, and the G2 Alike plug-in. The capture and analysis tools used here
  live in its `tools/`.
- **SynthEdit**: generic multi-synth editor
- **EmuUtility**: E-mu EOS sampler utility
- **GenBridge**, **MidiSyncTool**, **MidiSeqTool**: plug-ins on the same wrappers. This project started
  from MidiSeqTool's skeleton.

## Building

```
./do-plugin            # VST3 and Audio Unit, and installs them
./do-plugin au         # one format
./do-plugin --no-install
tools/do-dcocheck      # offline check of the oscillator law
./do-uncrustify        # after editing sources
```

The VST3 half needs the VST3 SDK at `~/Documents/vst3sdk` (or `$VST3_SDK`); the Audio Unit needs none.

## Licence

GPLv3 - see [`LICENSE`](LICENSE). Third-party components and their redistribution obligations are in
[`THIRD_PARTY.md`](THIRD_PARTY.md).

## Releasing

    ./do-release 0.1.0-beta.1     # the first release (there is no tag yet)
    ./do-release beta             # after that: beta / patch / minor / major / final bump the newest V* tag

Builds both plug-ins (universal, ad-hoc signed) into a `.dmg` on the Desktop with a `Read Me First.txt` (installing,
clearing the quarantine) and the licence. It never tags: it prints the `git tag` command to run once the `.dmg` has
been checked. Needs the VST3 SDK, as `do-plugin` does.
