#!/bin/zsh
# The amp-envelope session: attack, decay and release at every 8th value, each long enough for its stage,
# then the sustain level law. Writes to $1 (default /Volumes/ext-ssd/Captures/Pulse2/192k/env).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-/Volumes/ext-ssd/Captures/Pulse2/192k/env}"
span() { local v=$1; if (( v <= 40 )); then print 1.5; elif (( v <= 64 )); then print 3; elif (( v <= 80 )); then print 6;
         elif (( v <= 96 )); then print 12; elif (( v <= 112 )); then print 25; else print 45; fi; }
VALUES=($(seq 0 8 120) 127)
for v in $VALUES; do t=$(span $v); "$HERE/env_capture.py" "$OUT" attack $v $t 1; done
for v in $VALUES; do t=$(span $v); "$HERE/env_capture.py" "$OUT" decay $v $t 1; done
for v in $VALUES; do t=$(span $v); "$HERE/env_capture.py" "$OUT" release $v 1 $t; done
for v in $VALUES; do "$HERE/env_capture.py" "$OUT" sustain $v 1.5 0.5; done
print done
