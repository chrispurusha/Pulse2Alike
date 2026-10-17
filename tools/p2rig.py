#!/usr/bin/env python3
# The capture rig for the Pulse 2 (design §5): MIDI over USB through tools/midisend, audio through
# G2-Edit's tools/capture. Import it, or run it to put the test sound into the edit buffer.
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
MIDISEND = os.path.join(HERE, 'midisend')
CAPTURE = os.path.join(HERE, '..', '..', 'G2-Edit', 'tools', 'capture')
PORT = 'Pulse2'
CHANNEL = 12                     # the instrument's, 1-indexed
IN_CHANNELS = '6,7'              # Fireface inputs 7/8 = Pulse 2 L/R
EXT_OUT_CHANNEL = 5              # Fireface output 6 = EXT IN

CC = dict(osc1_shape=34, osc1_pw=35, osc1_semi=70, osc1_detune=71, osc1_keytrack=73, osc1_level=45,
          osc2_shape=38, osc2_pw=39, osc2_semi=36, osc2_detune=37, osc2_keytrack=40, osc2_level=46,
          osc3_shape=44, osc3_routing=72, osc3_semi=42, osc3_detune=43, osc3_sync=41, osc3_level=47,
          noise=48, cutoff=50, resonance=56, vcf_type=49, vcf_env=52, vcf_keytrack=51, vcf_velocity=53,
          drive=76, drive_curve=77, pan=59, volume=57, vca_velocity=58,
          envf_a=14, envf_d=15, envf_s=16, envf_r=17, envf_loop=74, envf_trigger=29,
          enva_a=18, enva_d=19, enva_s=20, enva_r=21, enva_loop=75, enva_trigger=31,
          glide_rate=5, glide_mode=62, arp_active=79, arp_range=80, arp_tempo=81, arp_clock=82, arp_mode=83, arp_step=84,
          arp_swing=85, arp_delay=86, arp_length=87, arp_accent=88, unison_detune=102, osc1_fade=103, osc2_fade=104)

CC_LFO1_SPEED = 24
CC_LFO1_SHAPE = 25

MOD_SOURCES = (108, 111, 114, 117, 90, 93, 96, 99)
MOD_AMOUNTS = (109, 112, 115, 118, 91, 94, 97, 100)

# One oscillator, everything else silent or neutral; bipolar dials at 64 (= 0); envelopes as a gate.
TEST_SOUND = dict(osc1_shape=1, osc1_pw=64, osc1_semi=64, osc1_detune=64, osc1_keytrack=1, osc1_level=127,
                  osc2_shape=1, osc2_pw=64, osc2_semi=64, osc2_detune=64, osc2_keytrack=1, osc2_level=0,
                  osc3_shape=0, osc3_routing=0, osc3_semi=64, osc3_detune=64, osc3_sync=0, osc3_level=0, noise=0,
                  cutoff=127, resonance=0, vcf_type=0, vcf_env=64, vcf_keytrack=64, vcf_velocity=64,
                  drive=0, drive_curve=0, pan=64, volume=100, vca_velocity=64,
                  envf_a=0, envf_d=0, envf_s=127, envf_r=0, envf_loop=0, envf_trigger=0,
                  enva_a=0, enva_d=0, enva_s=127, enva_r=0, enva_loop=0, enva_trigger=0,
                  glide_rate=0, glide_mode=0, arp_active=0, unison_detune=0, osc1_fade=0, osc2_fade=0)


def hexmsg(*b):
    return ''.join('%02x' % v for v in b)


def send(*items):
    subprocess.run([MIDISEND, PORT, *items], check=True)


def cc_items(settings):
    items = []
    for name, value in settings.items():
        items.append(hexmsg(0xB0 | (CHANNEL - 1), CC[name] if isinstance(name, str) else name, value))
    return items


def set_sound(overrides=None):
    settings = dict(TEST_SOUND)
    settings.update(overrides or {})
    items = cc_items(settings)
    items += [hexmsg(0xB0 | (CHANNEL - 1), cc, 0) for cc in MOD_SOURCES]
    items += [hexmsg(0xB0 | (CHANNEL - 1), cc, 64) for cc in MOD_AMOUNTS]
    send(*items)


def note_items(note, seconds, velocity=100):
    return [hexmsg(0x90 | (CHANNEL - 1), note, velocity), 'sleep:%d' % int(seconds * 1000),
            hexmsg(0x80 | (CHANNEL - 1), note, 0)]


def capture(path, seconds, rate=96000):
    """Starts a capture in the background; wait() the result. It starts 0.06-0.6 s late - align on the signal."""
    return subprocess.Popen([CAPTURE, '--device', 'Fireface', '--out', path, '--seconds', str(seconds),
                             '--rate', str(rate), '--channels', IN_CHANNELS],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


if __name__ == '__main__':
    set_sound()
    print('test sound sent')


# Sound bytes with no CC (the LFO phases), by row in the instrument's parameter order
SOUND_BYTE = dict(lfo1_phase=81, lfo2_phase=82)
P2DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p2dump')


def set_bytes(values):
    """Sets sound bytes no CC reaches: reads the edit buffer back, changes them, and sends it to the EDIT BUFFER
    (7F 00, whatever the reply said) - a dump with a slot number would be stored to flash."""
    import glob, tempfile
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([P2DUMP, PORT, d, 'edit'], check=True, capture_output=True)
        dump = bytearray(open(glob.glob(os.path.join(d, 'edit*.syx'))[0], 'rb').read())
    if len(dump) != 137 or dump[0] != 0xF0 or dump[4] != 0x10:
        raise RuntimeError('no sound dump from the edit buffer')
    dump[5], dump[6] = 0x7F, 0x00
    for name, v in values.items():
        dump[7 + SOUND_BYTE[name]] = v
    dump[135] = sum(dump[1:135]) & 0x7F
    send(dump.hex())


def set_step_bytes(values):
    """The 16 arpeggiator steps (rows 90-105), through the edit buffer like set_bytes."""
    for i, v in enumerate(values):
        SOUND_BYTE['arp_step_%d' % i] = 90 + i
    set_bytes({'arp_step_%d' % i: v for i, v in enumerate(values)})
