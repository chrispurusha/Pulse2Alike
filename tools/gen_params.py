# Generates plugin/p2Params.c/.h: every parameter of the instrument, as its display names them, and the panel
# pages that show them. usage: /usr/bin/python3 tools/gen_params.py   (then ./do-uncrustify)
SHAPE1=['PWM','SAW','TRI','APW','UNISON-M','UNISON-P','UNIAPW-M','UNIAPW-P','PARA-8','PARA-4']
SHAPE2=['PWM','SAW','TRI','X3-PWM','X1-PWM']
SHAPE3=['SQR','SAW','TRI','EXT','FB']
ROUTE3=['MIX','LEVEL2','VCF','DRIVE']
OFFON=['OFF','ON']
GLIDE=['OFF','NORM','FNGR','FNON','FOFF']
TRIG=['SNG1','SNG2','RET1','RET2','RET3']
LOOP=['OFF','A-D','D-D']
PHASE=['FREE','RAND','0','90','180','270']
LFOSHAPE=['SINE','TRI','SAW','SQR','S&H','sSIN','sTRI','sSAW','sSQR','sS&H']
FTYPE=['LP24','LP12','BP12','HP12']
CURVE=['NONE','TUBE','FUZZ','FX']
SRC=['OFF','LFO1','LFO1*MODW','LFO1*PRS','LFO2','LFO2*ENVA','ENVF','ENVA','VELOCITY','KEYTRACK','PITCH FLW','PITCHBEND','MODWHEEL','PRESSURE','BREATH CT','CONTROL-X','V.RELEASE','M-ACCU','M-PRODUCT','M-DELAY','M-SMOOTH','M-MIN','M-MAX','K-HIGHEST','K-LOWEST']
TGT=['PITCH','OSC1 PITCH','OSC2 PITCH','OSC3 PITCH','PULSEWIDTH1','PULSEWIDTH2','OSC1 LEVEL','OSC2 LEVEL','OSC3 LEVEL','NOISE LEVEL','CUTOFF','RESONANCE','VOLUME','PANNING','LFO1 SPEED','MOD1 AMOUNT','DRIVE','GLIDE RATE','ENVF RATES','ENVA RATES','UNISON DET','PARA FADE1','PARA FADE2','ARP SWING','CV OUT','M-ACCU','M-PRODUCT','M-DELAY','M-SMOOTH','M-MIN','M-MAX','VCF ENV AMT']
ARPMODE=['UP','DOWN','ALT','RAND','#UP','#DWN','#ALT']
OVS=['1x','2x','4x']
ARPACT=['OFF','ON','HOLD']
CLOCK=['1/1','3/4','2/3','1/2','3/8','1/3','1/4','3/16','1/6','1/8','3/32','1/12','1/16','3/64','1/24','1/32','3/128','1/48','1/64','1/96']
TEMPO=[str(46 + 2 * i) for i in range(128)]                      # BPM, measured: 46 + 2 per step
DURATION=['12.5%','18.8%','25%','37.5%','50%','75%','100%','150%','200%','300%','400%','600%','800%','1200%','1600%']
SWING=['%d%%' % (v - 14) for v in range(14, 115)]
DELAY=['%+d%%' % (v - 64) for v in range(14, 115)]
ONE_UP=lambda n: [str(i + 1) for i in range(n)]

# (id, title, short, lo, hi, default, kind, names, displayBase, continuous)
# kind: dial | list | bi (shows value-64) ; existing ids 0..10 keep their order and ranges
P=[]
def add(i,t,s,lo,hi,d,kind='dial',names=None,base=None,cont=False,flags=None,midi='SYNTHLIB_MIDI_NONE'):
    P.append(dict(id=i,title=t,short=s,lo=lo,hi=hi,d=d,kind=kind,names=names,base=(lo if base is None else base),cont=cont,flags=flags,midi=midi))
# existing
add('Osc1Shape','Osc 1 Shape','Shape',0,9,1,'list',SHAPE1)
add('Osc1Width','Osc 1 Pulse Width','Width',0,127,64)
add('Osc1Level','Osc 1 Level','Level',0,127,127)
add('Osc2Shape','Osc 2 Shape','Shape',0,4,1,'list',SHAPE2)
add('Osc2Width','Osc 2 Pulse Width','Width',0,127,64)
add('Osc2Semitone','Osc 2 Semitone','Semi',-48,48,0)
add('Osc2Level','Osc 2 Level','Level',0,127,0)
add('Volume','Volume','Volume',0,127,100,midi='7')       # CC 7 is the sound's volume on the instrument
add('Cutoff','Cutoff','Cutoff',0,127,80,cont=True)
add('Resonance','Resonance','Reso',0,127,0,cont=True)
add('FilterType','Filter Type','Type',0,3,0,'list',FTYPE)
# appended
add('Osc1Semitone','Osc 1 Semitone','Semi',-48,48,0)
add('Osc1Detune','Osc 1 Detune','Detune',0,127,64,'bi')
add('Osc1Keytrack','Osc 1 Keytrack','Keytrk',0,1,1,'list',OFFON)
add('Osc2Detune','Osc 2 Detune','Detune',0,127,64,'bi')
add('Osc2Keytrack','Osc 2 Keytrack','Keytrk',0,1,1,'list',OFFON)
add('Osc3Shape','Osc 3 Shape','Shape',0,4,0,'list',SHAPE3)
add('Osc3Routing','Osc 3 Routing','Route',0,3,0,'list',ROUTE3)
add('Osc3Semitone','Osc 3 Semitone','Semi',-48,48,0)
add('Osc3Detune','Osc 3 Detune','Detune',0,127,64,'bi')
add('Osc3Sync','Osc 3 Sync to Osc 2','Sync',0,1,0,'list',OFFON)
add('Osc3Level','Osc 3 Level','Level',0,127,0)
add('NoiseLevel','Noise Level','Noise',0,127,0)
add('GlideRate','Glide Rate','Rate',0,127,0)
add('GlideMode','Glide Mode','Mode',0,4,0,'list',GLIDE)
add('UnisonDetune','Unison Detune','Unison',0,127,0)
add('FilterEnvAmount','Filter Env Amount','Env',0,127,64,'bi')
add('FilterKeytrack','Filter Keytrack','Keytrk',0,127,64,'bi')
add('FilterVelocity','Filter Velocity','Velo',0,127,64,'bi')
add('Drive','Drive','Drive',0,127,0)
add('DriveCurve','Drive Curve','Curve',0,3,0,'list',CURVE)
add('Pan','Pan','Pan',0,127,64,'bi')
add('AmpVelocity','Amp Velocity','Velo',0,127,64,'bi')
for e,n in (('EnvF','Filter Env'),('EnvA','Amp Env')):
    add(e+'Attack',n+' Attack','Attack',0,127,0)
    add(e+'Decay',n+' Decay','Decay',0,127,64)
    add(e+'Sustain',n+' Sustain','Sustain',0,127,127 if e=='EnvA' else 0)
    add(e+'Release',n+' Release','Release',0,127,16)
    add(e+'Loop',n+' Loop','Loop',0,2,0,'list',LOOP)
    add(e+'Trigger',n+' Trigger','Trigger',0,4,0,'list',TRIG)
add('Lfo1Speed','LFO 1 Speed','Speed',0,127,64)
add('Lfo1Shape','LFO 1 Shape','Shape',0,9,0,'list',LFOSHAPE)
add('Lfo1Phase','LFO 1 Phase','Phase',0,5,0,'list',PHASE)
add('Lfo2Speed','LFO 2 Speed','Speed',0,127,64)
add('Lfo2Delay','LFO 2 Delay','Delay',0,127,0)
add('Lfo2Phase','LFO 2 Phase','Phase',0,5,0,'list',PHASE)
for m in range(1,9):
    add('Mod%dSource'%m,'Mod %d Source'%m,'Source',0,24,0,'list',SRC)
    add('Mod%dAmount'%m,'Mod %d Amount'%m,'Amount',0,127,64,'bi')
    add('Mod%dTarget'%m,'Mod %d Target'%m,'Target',0,31,0,'list',TGT)
add('ArpActive','Arp Active','Arp',0,2,0,'list',ARPACT)
add('ArpRange','Arp Range','Range',0,9,0,names=ONE_UP(10))
add('ArpTempo','Arp Tempo','Tempo',0,127,37,names=TEMPO)
add('ArpClock','Arp Clock','Clock',0,19,12,'list',CLOCK)
add('ArpPattern','Arp Pattern','Pattern',0,14,0)
add('ArpMode','Arp Mode','Mode',0,6,0,'list',ARPMODE)
add('ArpStep','Arp Step Duration','Step',0,14,6,names=DURATION)
add('ArpSwing','Arp Swing','Swing',14,114,64,names=SWING)
add('ArpDelay','Arp Delay','Delay',14,114,64,names=DELAY)
add('ArpLength','Arp Pattern Length','Length',0,15,15,names=ONE_UP(16))
add('BendUp','Bend Up','Bend +',0,36,2)
add('BendDown','Bend Down','Bend -',0,36,2)
add('Osc1Fade','Osc 1 Env A Fade','Fade 1',0,127,0)
add('Osc2Fade','Osc 2 Env A Fade','Fade 2',0,127,0)
add('Oversample','Oversampling','OvrSmp',0,2,2,'list',OVS)
add('Anomalies','Anomalies','Anomalies',0,1,1,'list',OFFON)
add('Master','Master Volume','Master',0,127,127)
# notes §5: program change and bank select (CC 32), as the instrument takes them; never saved
add('Program','Program','Program',0,127,0,flags='SYNTHLIB_PARAM_PROGRAM | SYNTHLIB_PARAM_HIDDEN | SYNTHLIB_PARAM_NO_SAVE')
add('Bank','Bank Select','Bank',0,127,0,flags='SYNTHLIB_PARAM_HIDDEN | SYNTHLIB_PARAM_NO_SAVE',midi='32')
# notes §6: the performance controls, as a host delivers them (IMidiMapping); played, never saved
PERF='SYNTHLIB_PARAM_HIDDEN | SYNTHLIB_PARAM_NO_SAVE'
add('PitchBend','Pitch Bend','Bend',-1,1,0,cont=True,flags=PERF,midi='SYNTHLIB_MIDI_PITCH_BEND')
add('ModWheel','Mod Wheel','ModWhl',0,127,0,cont=True,flags=PERF,midi='SYNTHLIB_MIDI_MOD_WHEEL')
add('Pressure','Pressure','Press',0,127,0,cont=True,flags=PERF,midi='SYNTHLIB_MIDI_AFTERTOUCH')
add('Breath','Breath','Breath',0,127,0,cont=True,flags=PERF,midi='SYNTHLIB_MIDI_BREATH')
add('Sustain','Sustain Pedal','Sustain',0,127,0,cont=True,flags=PERF,midi='SYNTHLIB_MIDI_SUSTAIN')
# notes §7: the arpeggiator's 16 steps, one byte each (event in bits 0-3, time in 4-5, glide in 6) and its accent;
# saved with the sound, not shown until there is a step editor
for i in range(1, 17):
    add('ArpStep%d' % i, 'Arp Step %d' % i, 'Step %d' % i, 0, 127, 50, flags='SYNTHLIB_PARAM_HIDDEN')
add('ArpAccent','Arp Accent Control','Accent',0,24,0,'list',SRC)


ROWS = ['Osc1Shape','Osc1Width','Osc1Semitone','Osc1Detune','Osc1Keytrack','Osc1Level',
        'Osc2Shape','Osc2Width','Osc2Semitone','Osc2Detune','Osc2Keytrack','Osc2Level',
        'Osc3Shape','Osc3Routing','Osc3Semitone','Osc3Detune','Osc3Sync','Osc3Level',
        'Lfo1Speed','Lfo1Shape','Lfo2Speed','Lfo2Delay','GlideRate','GlideMode',
        'EnvFAttack','EnvFDecay','EnvFSustain','EnvFRelease','EnvFLoop','EnvFTrigger',
        'EnvAAttack','EnvADecay','EnvASustain','EnvARelease','EnvALoop','EnvATrigger',
        'ArpActive','ArpRange','ArpTempo','ArpClock','ArpPattern','ArpMode',
        'Cutoff','Resonance','FilterEnvAmount','FilterType','FilterKeytrack','FilterVelocity',
        'Drive','DriveCurve','Pan','NoiseLevel','Volume','AmpVelocity'] + \
       sum([['Mod%dSource' % m, 'Mod%dAmount' % m, 'Mod%dTarget' % m] for m in range(1, 9)], []) + \
       ['UnisonDetune','Osc1Fade','Osc2Fade','Lfo1Phase','Lfo2Phase',None,None,'BendUp','BendDown',
        'ArpStep','ArpSwing','ArpDelay'] + ['ArpStep%d' % i for i in range(1, 17)] + ['ArpLength', 'ArpAccent']
RAW_LOW = {'Osc1Semitone': 16, 'Osc2Semitone': 16, 'Osc3Semitone': 16}   # stored 16..112, shown -48..+48

PAGES=[
 ('OSCILLATORS',[('OSC 1',(0.30,0.55,0.85),['Osc1Shape','Osc1Width','Osc1Semitone','Osc1Detune','Osc1Keytrack','Osc1Level']),
                 ('OSC 2',(0.30,0.55,0.85),['Osc2Shape','Osc2Width','Osc2Semitone','Osc2Detune','Osc2Keytrack','Osc2Level']),
                 ('OSC 3',(0.30,0.55,0.85),['Osc3Shape','Osc3Routing','Osc3Semitone','Osc3Detune','Osc3Sync','Osc3Level']),
                 ('MIXER',(0.55,0.55,0.75),['NoiseLevel','UnisonDetune']),
                 ('GLIDE',(0.55,0.55,0.75),['GlideMode','GlideRate'])]),
 ('FILTER',[('FILTER',(0.90,0.55,0.20),['FilterType','Cutoff','Resonance']),
            ('MODULATION',(0.90,0.55,0.20),['FilterEnvAmount','FilterKeytrack','FilterVelocity'])]),
 ('AMP',[('AMP',(0.85,0.75,0.25),['Drive','DriveCurve','Volume','Pan','AmpVelocity']),
         ('MASTER',(0.65,0.65,0.65),['Master'])]),
 ('ENVELOPES',[('FILTER ENV',(0.90,0.55,0.20),['EnvFAttack','EnvFDecay','EnvFSustain','EnvFRelease','EnvFLoop','EnvFTrigger']),
               ('AMP ENV',(0.85,0.75,0.25),['EnvAAttack','EnvADecay','EnvASustain','EnvARelease','EnvALoop','EnvATrigger'])]),
 ('LFOS',[('LFO 1',(0.40,0.75,0.45),['Lfo1Shape','Lfo1Speed','Lfo1Phase']),
          ('LFO 2',(0.40,0.75,0.45),['Lfo2Speed','Lfo2Delay','Lfo2Phase'])]),
 ('MOD',[('MOD %d'%m,(0.70,0.45,0.75),['Mod%dSource'%m,'Mod%dAmount'%m,'Mod%dTarget'%m]) for m in range(1,9)]),
 ('ARP',[('ARPEGGIATOR',(0.65,0.65,0.65),['ArpActive','ArpMode','ArpRange','ArpClock','ArpTempo','ArpPattern']),
         ('TIMING',(0.65,0.65,0.65),['ArpStep','ArpSwing','ArpDelay','ArpLength','ArpAccent'])]),
 ('GLOBAL',[('PERFORMANCE',(0.65,0.65,0.65),['BendUp','BendDown','Osc1Fade','Osc2Fade']),
            ('PLUG-IN',(0.65,0.65,0.65),['Oversample','Anomalies'])]),
]

ids={p['id']:i for i,p in enumerate(P)}
def cname(n): return 'kP2Param'+n
def cstr(s): return '"'+s.replace('"','\\"')+'"'
H=[]; C=[]
H.append('''/*
 * Pulse2Alike - every parameter of the instrument, and the panel pages that show them.
 *
 * Copyright (C) 2026 Chris Turner <chris_purusha@icloud.com>
 *
 * This program is free software: you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
 * even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with this program. If
 * not, see <https://www.gnu.org/licenses/>.
 */
// Notes: Docs/code-notes/p2Params.md - "// notes §k" refers there.

#ifndef __P2_PARAMS_H__
#define __P2_PARAMS_H__

#include "synthlibPlugin.h"
#include "p2Draw.h"

// notes §1: appended to, never inserted into - ids are what projects save
enum {''')
for i,p in enumerate(P):
    H.append('    %s%s,'%(cname(p['id']),' = 0' if i==0 else ''))
H.append('    kP2ParamCount\n};\n')
H.append('extern const tSynthLibParam gP2Params[kP2ParamCount];')
H.append('extern const tP2Page        gP2Pages[];')
H.append('extern const uint32_t       gP2PageCount;\n')
H.append('// notes §3: the instrument\'s 128 sound bytes (a sound dump\'s data), mapped onto the parameters')
H.append('#define P2_SOUND_BYTES          (128)')
H.append('#define P2_SOUND_BYTE_UNUSED    (0xFFFFFFFFu)')
H.append('#define P2_SOUND_NAME_OFFSET    (113)')
H.append('#define P2_SOUND_NAME_LENGTH    (14)')
H.append('typedef struct {\n    uint32_t paramId;\n    int32_t  rawLow;\n} tP2SoundByte;')
H.append('extern const tP2SoundByte gP2SoundBytes[P2_SOUND_BYTES];\n')
H.append('// The entry names of a list parameter, NULL for a dial.')
H.append('const char * const * p2_param_names(uint32_t id);\n')
H.append('#endif // __P2_PARAMS_H__')

C.append(H[0].split('#ifndef')[0].replace('Notes: Docs/code-notes/p2Params.md - "// notes §k" refers there.','Notes: Docs/code-notes/p2Params.md - "// notes §k" refers there.'))
C.append('// GENERATED by tools/gen_params.py - edit that and rerun it, not this file.\n')
C.append('#include "p2Params.h"\n')
for p in P:
    if p['names']:
        C.append('static const char * const kNames%s[] = {%s};'%(p['id'],', '.join(cstr(n) for n in p['names'])))
C.append('\nconst tSynthLibParam gP2Params[kP2ParamCount] = {')
for p in P:
    n=p['hi']-p['lo']; dn=(p['d']-p['lo'])/n
    unit='eSynthLibUnitIndexed' if p['kind']=='list' else ('eSynthLibUnitSemitones' if 'Semitone' in p['id'] else 'eSynthLibUnitGeneric')
    steps=0 if p['cont'] else n
    flags=p['flags'] or ('SYNTHLIB_PARAM_LIST' if p['kind']=='list' else '0')
    C.append('    {%s, %s, %s, %s, %.1f, %.1f, %.6f, %d, %s, %s},'%(cname(p['id']),cstr(p['title']),cstr(p['short']),unit,p['lo'],p['hi'],dn,steps,p['midi'],flags))
C.append('};\n')
C.append('// The instrument\'s sound bytes, in order: which parameter each one is, and the raw value of its lowest step.')
C.append('const tP2SoundByte gP2SoundBytes[P2_SOUND_BYTES] = {')
for r in range(128):
    name = ROWS[r] if r < len(ROWS) else None
    if name is None:
        C.append('    {P2_SOUND_BYTE_UNUSED, 0},')
    else:
        C.append('    {%s, %d},' % (cname(name), RAW_LOW.get(name, P[ids[name]]['lo'])))
C.append('};\n')
C.append('const char * const * p2_param_names(uint32_t id) {\n    switch (id) {')
for p in P:
    if p['names']:
        C.append('    case %s: return kNames%s;'%(cname(p['id']),p['id']))
C.append('    default: return NULL;\n    }\n}\n')
# controls per section
sidx=0
for pg,secs in PAGES:
    for title,col,plist in secs:
        sidx+=1
        C.append('static const tP2Control kSection%d[] = {'%sidx)
        for pid in plist:
            p=P[ids[pid]]; n=p['hi']-p['lo']
            base=p['lo']-64 if p['kind']=='bi' else p['lo']
            kind='eP2ControlChoice' if p['kind']=='list' else 'eP2ControlDial'
            names=('kNames'+pid) if p['names'] else 'NULL'
            C.append('    {%s, %s, %s, %d, %.1f, %s},'%(cname(pid),cstr(p['short']),kind,n,base,names))
        C.append('};')
sidx=0
for i,(pg,secs) in enumerate(PAGES):
    C.append('static const tP2Section kPage%dSections[] = {'%i)
    for title,col,plist in secs:
        sidx+=1
        C.append('    {%s, {%.2f, %.2f, %.2f}, kSection%d, %d},'%(cstr(title),*col,sidx,len(plist)))
    C.append('};')
C.append('\nconst tP2Page gP2Pages[] = {')
for i,(pg,secs) in enumerate(PAGES):
    C.append('    {%s, kPage%dSections, %d},'%(cstr(pg),i,len(secs)))
C.append('};\nconst uint32_t gP2PageCount = sizeof(gP2Pages) / sizeof(gP2Pages[0]);')
import os
d=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plugin') + '/'
open(d+'p2Params.h','w').write('\n'.join(H)+'\n')
open(d+'p2Params.c','w').write('\n'.join(C)+'\n')
print(len(P),'params,',sidx,'sections,',len(PAGES),'pages')
