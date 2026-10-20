# p2Arp.c - notes

The arpeggiator, from the values the instrument's panel names, the manual's description of the modes, and timing
measured on the instrument (findings, "arpeggiator").

## 1. Clock and Step Duration
Clock values are the note lengths the panel names (1/1, 3/4, 2/3 ... 1/96), as steps in ticks at 96 to a quarter
note: 384 (1/1), 288, 256, 192, 144, 128, 96 (1/4), 72, 64, 48, 36, 32, 24 (1/16), 18, 16, 12, 9, 8, 6, 4 (1/96).
Step Duration is the percentage the panel shows, as the note's length in 32nds of the step: 4 (12.5%), 6, 8, 12,
16, 24, 32 (100%), 48 ... 512 (1600%), and a step's Time (25/50/75/100%) multiplies it.

## 2. A step's byte
Event in bits 0-3 (OFF, SOFT, NORM, HARD, EVEN, ODD, OCT+, 1ST, RESET), Time in bits 4-5, Glide in bit 6. The
initial pattern is 50 throughout: NORM, 100%, no glide (it is 50 in 6078 of the library's 6512 step bytes).

## 3. The note sequence
UP, DOWN, ALT and RAND take the held keys in pitch order; #UP, #DWN and #ALT in the order they were played (at
most 16, so a held chord can repeat a note). Range sets how many octaves (1-10). DOWN is UP reversed (from the top
octave down); ALT goes up and back without repeating the ends - as measured on the instrument with a chord over two
octaves; RAND picks from UP's sequence.

## 4. Keys
ON: the held keys are the sequence, and it stops when they are all up. HOLD: the sequence stays when the keys are
released, and the next key after that starts a new one.

## 5. Events
OFF plays nothing; SOFT −32 and HARD +64 on the velocity (127 at most - the plug-in's choice, not yet measured); EVEN and ODD play on alternate passes of the
pattern only; OCT+ an octave up; 1ST the first key played, at its own velocity; RESET restarts the sequence and
plays its first note. Every step uses up its place in the sequence, even one that plays nothing (measured: with step 2 OFF over
48 52 55 the passes are 48·55·48, 52·48·52, 55·52·55). The
velocity is the key's own.

## 6. Accent
Accent Control names a mod source; when it is higher than the step's velocity it replaces it, before SOFT/HARD.
A bipolar source (the LFOs, keytrack, pitch follow, bend) is centred on 64, as the instrument scales them.

## 7. The clock
On its own, the arp starts with the first key at Tempo (46 + 2 per step BPM, measured) and Delay can only make it
later. Following a host that is playing, it takes the host's tempo and keeps to its grid: the first step on the
next grid step, Delay moving the grid either way, and the pattern counted from the host's position so it keeps to
its bars. A jump in the host's position realigns it.

## 8. Swing
The first step of each pair takes Swing's share of the two (measured: (Swing − 14)%; 64 is straight, 80 the
manual's 66% triplet feel). At the ends one step of the pair has no length.

## 9. #ALT
On the instrument #ALT goes up through the keys once and then swings between the top two for good (measured, with
the default steps: 48 52 55 60 64 67 64 67 64 67 ...). With Anomalies on the plug-in does the same; off, #ALT is
ALT in the order played.

## 10. Notes that outlast their step
A step's length (Step Duration × its Time) can run past the next step, up to 16 steps at 1600%, and Swing makes
the second step of a pair shorter than the first, so even 100% overlaps there. Every note playing is kept with its
own end until it ends; the next step's note starts before a due note ends, so the join is legato for glide. (Only
one note used to be kept: a note still sounding when the next began was forgotten, never ended, and hung in the
voice's key stack after the arp stopped - into the next sound.)

## 11. Keys held and keys kept
The arp knows every key, whether it is on or not, and which of them are physically down. Turning it ON keeps only
the keys that are down; a chord HOLD kept after its keys were let go is dropped.
