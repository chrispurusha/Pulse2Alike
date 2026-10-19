# p2Hardware.c

## 1. Finding the instrument
The first CoreMIDI destination whose name contains "pulse", in any case - the Pulse 2's USB port is "Pulse2". One
client and output port per process, made on first use, handed to SynthLib's `synthlib_midi_send_to()`.

## 2. The edit buffer only
A dump addressed to a slot (bytes 5-6 = bank, program) is stored to that slot's flash; one addressed 7F 00 only
replaces the edit buffer. Library files carry their slot number, so every send readdresses the dump to 7F 00 and
recomputes the checksum (the sum of bytes 1-134, low seven bits) whatever it came with. Checked on the instrument
2026-10-19: a dump carrying slot 05 0B arrived in the edit buffer byte for byte.
