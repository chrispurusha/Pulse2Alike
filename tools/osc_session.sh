#!/bin/zsh
# The oscillator session (design §5.1): every shape of every oscillator at several levels and pitches, then the
# level, detune and semitone laws. Writes to $1 (default /Volumes/ext-ssd/Captures/Pulse2/192k/osc).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-/Volumes/ext-ssd/Captures/Pulse2/192k/osc}"
mkdir -p "$OUT"
cap() { "$HERE/osc_capture.py" "$OUT/$1.wav" "${@:2}" > /dev/null; print -n "$1 "; }
NOTES=notes=24,36,48,60,72,84,96,108
SHAPES1=(pwm saw tri)
for s in 0 1 2; do for l in 127 64 32; do cap osc1_${SHAPES1[$((s+1))]}_l$l $s volume=40 osc1_level=$l $NOTES; done; done
SHAPES2=(pwm saw tri x3pwm x1pwm)
for s in 0 1 2 3 4; do for l in 127 64; do cap osc2_${SHAPES2[$((s+1))]}_l$l 0 volume=40 osc1_level=0 osc2_shape=$s osc2_level=$l $NOTES; done; done
SHAPES3=(sqr saw tri ext fb)
for s in 0 1 2 4; do for l in 127 64; do cap osc3_${SHAPES3[$((s+1))]}_l$l 0 volume=40 osc1_level=0 osc3_shape=$s osc3_level=$l $NOTES; done; done
cap noise_l127 0 volume=40 osc1_level=0 noise=127 notes=60
for l in $(seq 0 8 120) 127; do cap law_level_$l 1 volume=40 osc1_level=$l notes=48; done
for d in $(seq 0 8 120) 127; do cap law_detune_$d 1 volume=40 osc1_detune=$d notes=60; done
for t in $(seq 16 8 112); do cap law_semi_$t 1 volume=40 osc1_semi=$t notes=60; done
print "\ndone"
