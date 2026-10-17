# play.c - notes

The playing half of the EXT IN rig. `tone` (G2-Edit) plays one sine; this plays any designed signal: a sweep,
noise, a multitone. Same AUHAL approach as `tone`, at the device's own rate and channel count, silent on
every channel not named.

Build: `cc -O2 -Wall -o play play.c -framework CoreAudio -framework AudioToolbox -framework CoreFoundation`

## 1. The WAV reader
Mono, 32-bit integer or float only, which is what `filter_sweep.py` writes. The file's rate has to equal the
device's: there is no resampling, and a mismatch is refused, not played at the wrong pitch.
