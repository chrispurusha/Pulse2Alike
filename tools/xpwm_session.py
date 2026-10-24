#!/usr/bin/python3
# Osc 2's X3-PWM and X1-PWM (shape 3 and 4; the manual: osc 2's pulse XOR osc 3's / osc 1's wave): what they combine.
# Osc 2 at note 48, the other oscillator 7 semitones up, so the products land on sum and difference frequencies whose
# sizes do not depend on the free-running phases. Filter open, everything else silent. usage: xpwm_session.py
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2rig

OUT = '/Volumes/ext-ssd/Captures/Pulse2/192k/xpwm'
NOTE, HOLD = 48, 2.5
BASE = dict(osc1_level=0, osc2_level=127, osc3_level=0, noise=0, cutoff=127, resonance=0, volume=40,
            osc1_semi=64 + 7, osc3_semi=64 + 7)
CASES = {
    # references: osc 2's own pulse, and the other oscillators alone
    'ref_o2_pwm_w64': dict(osc2_shape=0, osc2_pw=64),
    'ref_o2_pwm_w100': dict(osc2_shape=0, osc2_pw=100),
    'ref_o2_saw': dict(osc2_shape=1),
    'ref_o3_sqr': dict(osc2_level=0, osc3_shape=0, osc3_level=127),
    'ref_o1_pwm_w64': dict(osc2_level=0, osc1_shape=0, osc1_pw=64, osc1_level=127),
    # X3-PWM: osc 3's shape and level, osc 2's width
    'x3_w64_sqr_l0': dict(osc2_shape=3, osc2_pw=64, osc3_shape=0),
    'x3_w64_sqr_l127': dict(osc2_shape=3, osc2_pw=64, osc3_shape=0, osc3_level=127),
    'x3_w64_saw_l0': dict(osc2_shape=3, osc2_pw=64, osc3_shape=1),
    'x3_w64_tri_l0': dict(osc2_shape=3, osc2_pw=64, osc3_shape=2),
    'x3_w100_sqr_l0': dict(osc2_shape=3, osc2_pw=100, osc3_shape=0),
    'x3_w127_sqr_l0': dict(osc2_shape=3, osc2_pw=127, osc3_shape=0),
    'x3_w20_sqr_l0': dict(osc2_shape=3, osc2_pw=20, osc3_shape=0),
    'x3_w0_sqr_l0': dict(osc2_shape=3, osc2_pw=0, osc3_shape=0),
    # X1-PWM: osc 1's shape and width
    'x1_w64_pwm64': dict(osc2_shape=4, osc2_pw=64, osc1_shape=0, osc1_pw=64),
    'x1_w64_pwm100': dict(osc2_shape=4, osc2_pw=64, osc1_shape=0, osc1_pw=100),
    'x1_w64_saw': dict(osc2_shape=4, osc2_pw=64, osc1_shape=1),
    'x1_w64_tri': dict(osc2_shape=4, osc2_pw=64, osc1_shape=2),
    'x1_w100_pwm64': dict(osc2_shape=4, osc2_pw=100, osc1_shape=0, osc1_pw=64),
    'x1_w64_pwm64_l127': dict(osc2_shape=4, osc2_pw=64, osc1_shape=0, osc1_pw=64, osc1_level=127),
    # same pitch: is the XOR phase-locked to osc 2 (a fixed shape) or free (a slow beat)?
    'x3_w64_sqr_unison': dict(osc2_shape=3, osc2_pw=64, osc3_shape=0, osc3_semi=64),
}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, s in CASES.items():
        hw = os.path.join(OUT, 'hw_%s.wav' % name)
        if os.path.exists(hw):
            continue
        p2rig.set_sound(dict(BASE, **s))
        time.sleep(0.3)
        cap = p2rig.capture(hw, HOLD + 1.5, 192000)
        time.sleep(0.8)
        p2rig.send(*p2rig.note_items(NOTE, HOLD))
        cap.communicate()
        print(name, flush=True)
