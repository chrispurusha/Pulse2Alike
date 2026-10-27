/*
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
enum {
    kP2ParamOsc1Shape = 0,
    kP2ParamOsc1Width,
    kP2ParamOsc1Level,
    kP2ParamOsc2Shape,
    kP2ParamOsc2Width,
    kP2ParamOsc2Semitone,
    kP2ParamOsc2Level,
    kP2ParamVolume,
    kP2ParamCutoff,
    kP2ParamResonance,
    kP2ParamFilterType,
    kP2ParamOsc1Semitone,
    kP2ParamOsc1Detune,
    kP2ParamOsc1Keytrack,
    kP2ParamOsc2Detune,
    kP2ParamOsc2Keytrack,
    kP2ParamOsc3Shape,
    kP2ParamOsc3Routing,
    kP2ParamOsc3Semitone,
    kP2ParamOsc3Detune,
    kP2ParamOsc3Sync,
    kP2ParamOsc3Level,
    kP2ParamNoiseLevel,
    kP2ParamGlideRate,
    kP2ParamGlideMode,
    kP2ParamUnisonDetune,
    kP2ParamFilterEnvAmount,
    kP2ParamFilterKeytrack,
    kP2ParamFilterVelocity,
    kP2ParamDrive,
    kP2ParamDriveCurve,
    kP2ParamPan,
    kP2ParamAmpVelocity,
    kP2ParamEnvFAttack,
    kP2ParamEnvFDecay,
    kP2ParamEnvFSustain,
    kP2ParamEnvFRelease,
    kP2ParamEnvFLoop,
    kP2ParamEnvFTrigger,
    kP2ParamEnvAAttack,
    kP2ParamEnvADecay,
    kP2ParamEnvASustain,
    kP2ParamEnvARelease,
    kP2ParamEnvALoop,
    kP2ParamEnvATrigger,
    kP2ParamLfo1Speed,
    kP2ParamLfo1Shape,
    kP2ParamLfo1Phase,
    kP2ParamLfo2Speed,
    kP2ParamLfo2Delay,
    kP2ParamLfo2Phase,
    kP2ParamMod1Source,
    kP2ParamMod1Amount,
    kP2ParamMod1Target,
    kP2ParamMod2Source,
    kP2ParamMod2Amount,
    kP2ParamMod2Target,
    kP2ParamMod3Source,
    kP2ParamMod3Amount,
    kP2ParamMod3Target,
    kP2ParamMod4Source,
    kP2ParamMod4Amount,
    kP2ParamMod4Target,
    kP2ParamMod5Source,
    kP2ParamMod5Amount,
    kP2ParamMod5Target,
    kP2ParamMod6Source,
    kP2ParamMod6Amount,
    kP2ParamMod6Target,
    kP2ParamMod7Source,
    kP2ParamMod7Amount,
    kP2ParamMod7Target,
    kP2ParamMod8Source,
    kP2ParamMod8Amount,
    kP2ParamMod8Target,
    kP2ParamArpActive,
    kP2ParamArpRange,
    kP2ParamArpTempo,
    kP2ParamArpClock,
    kP2ParamArpPattern,
    kP2ParamArpMode,
    kP2ParamArpStep,
    kP2ParamArpSwing,
    kP2ParamArpDelay,
    kP2ParamArpLength,
    kP2ParamBendUp,
    kP2ParamBendDown,
    kP2ParamOsc1Fade,
    kP2ParamOsc2Fade,
    kP2ParamOversample,
    kP2ParamAnomalies,
    kP2ParamMaster,
    kP2ParamProgram,
    kP2ParamBank,
    kP2ParamPitchBend,
    kP2ParamModWheel,
    kP2ParamPressure,
    kP2ParamBreath,
    kP2ParamSustain,
    kP2ParamArpStep1,
    kP2ParamArpStep2,
    kP2ParamArpStep3,
    kP2ParamArpStep4,
    kP2ParamArpStep5,
    kP2ParamArpStep6,
    kP2ParamArpStep7,
    kP2ParamArpStep8,
    kP2ParamArpStep9,
    kP2ParamArpStep10,
    kP2ParamArpStep11,
    kP2ParamArpStep12,
    kP2ParamArpStep13,
    kP2ParamArpStep14,
    kP2ParamArpStep15,
    kP2ParamArpStep16,
    kP2ParamArpAccent,
    kP2ParamHiss,
    kP2ParamHwLink,
    kP2ParamHwChannel,
    kP2ParamMasterTune,
    kP2ParamTranspose,
    kP2ParamCount
};

extern const tSynthLibParam gP2Params[kP2ParamCount];
extern const tP2Page        gP2Pages[];
extern const uint32_t       gP2PageCount;

// notes §3: the instrument's 128 sound bytes (a sound dump's data), mapped onto the parameters
#define P2_SOUND_BYTES          (128)
#define P2_SOUND_BYTE_UNUSED    (0xFFFFFFFFu)
#define P2_SOUND_NAME_OFFSET    (113)
#define P2_SOUND_NAME_LENGTH    (14)
typedef struct {
    uint32_t paramId;
    int32_t  rawLow;
} tP2SoundByte;
extern const tP2SoundByte   gP2SoundBytes[P2_SOUND_BYTES];

// The entry names of a list parameter, NULL for a dial.
const char * const * p2_param_names(uint32_t id);

#endif // __P2_PARAMS_H__
