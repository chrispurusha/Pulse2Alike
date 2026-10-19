// Renders a note through the plug-in's own engine, offline: a .syx sound loaded, one note held, a WAV written.
// usage: p2render <sound.syx|-> <note> <hold_s> <tail_s> <out.wav> [rate] [title=plain ...]   ("-" keeps the defaults)
//        <note> may be a chord, "48,52,55", or a sequence of note:start:length in seconds, "48:0:0.4,60:0.6:0.15"
//        (with a sequence, hold_s is the length before the tail)
//        a title is the parameter's, matched without case or spaces: osc1level=127 drivecurve=1
// Build: tools/do-p2render
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "synthlibPlugin.h"
#include "p2Params.h"
#include "p2Patch.h"

#define RENDER_GAIN    (0.1)

// What the wrappers would provide; the engine does not need them offline.
void synthlib_plugin_param_edited(void * inst, uint32_t id, double normalized) {
    (void)inst;
    (void)id;
    (void)normalized;
}

// "Osc 1 Level" and "osc1level" are the same parameter
static bool title_matches(const char * title, const char * key, size_t keyLen) {
    size_t k = 0;

    for (const char * t = title; *t != '\0'; t++) {
        if (*t == ' ') {
            continue;
        }

        if ((k >= keyLen) || (tolower((unsigned char)*t) != tolower((unsigned char)key[k]))) {
            return false;
        }
        k++;
    }

    return k == keyLen;
}

static bool apply_override(double values[kP2ParamCount], const char * arg) {
    const char * eq = strchr(arg, '=');

    for (uint32_t i = 0; (eq != NULL) && (i < kP2ParamCount); i++) {
        if (title_matches(gP2Params[i].title, arg, (size_t)(eq - arg))) {
            double span = gP2Params[i].plainMax - gP2Params[i].plainMin;

            values[i] = (span > 0.0) ? ((atof(eq + 1) - gP2Params[i].plainMin) / span) : 0.0;
            return true;
        }
    }

    return false;
}

static void write_wav(const char * path, const float * x, size_t n, int rate) {
    FILE *   f = fopen(path, "wb");
    uint32_t dataBytes = (uint32_t)(n * 4), riff = 36 + dataBytes, fmtLen = 16, rate32 = (uint32_t)rate, byteRate = rate32 * 4;
    uint16_t pcm = 1, ch = 1, align = 4, bits = 32;

    fwrite("RIFF", 1, 4, f);
    fwrite(&riff, 4, 1, f);
    fwrite("WAVEfmt ", 1, 8, f);
    fwrite(&fmtLen, 4, 1, f);
    fwrite(&pcm, 2, 1, f);
    fwrite(&ch, 2, 1, f);
    fwrite(&rate32, 4, 1, f);
    fwrite(&byteRate, 4, 1, f);
    fwrite(&align, 2, 1, f);
    fwrite(&bits, 2, 1, f);
    fwrite("data", 1, 4, f);
    fwrite(&dataBytes, 4, 1, f);

    for (size_t i = 0; i < n; i++) {
        // RENDERED 20 dB DOWN: the plug-in's float output may pass full scale (the host does not clip it), and a
        // clipped render scores as a difference. The comparisons level-match, so the scale is immaterial.
        double  v = x[i] * RENDER_GAIN;

        v = v > 1.0 ? 1.0 : (v < -1.0 ? -1.0 : v);
        int32_t s = (int32_t)(v * 2147483647.0);

        fwrite(&s, 4, 1, f);
    }

    fclose(f);
}

int main(int argc, char ** argv) {
    if (argc < 6) {
        fprintf(stderr, "usage: p2render <sound.syx|-> <note> <hold_s> <tail_s> <out.wav> [rate]\n");
        return 2;
    }
    const tSynthLibPluginDesc * d                              = &synthlib_plugin_variants()->variants[0];
    int                         notes[32], noteCount = 0;
    double                      starts[32], lengths[32];
    float                       velocity                       = 100.0f / 127.0f; // "48" or a chord, "48,52,55"

    bool                        sequence                       = (strchr(argv[2], ':') != NULL);

    for (char * tok = strtok(argv[2], ","); (tok != NULL) && (noteCount < 32); tok = strtok(NULL, ",")) {
        char * c1 = strchr(tok, ':');

        notes[noteCount]   = atoi(tok);
        starts[noteCount]  = (c1 != NULL) ? atof(c1 + 1) : 0.0;
        lengths[noteCount] = ((c1 != NULL) && (strchr(c1 + 1, ':') != NULL)) ? atof(strchr(c1 + 1, ':') + 1) : -1.0;
        noteCount++;
    }

    int                         note                           = notes[0];
    double                      hold = atof(argv[3]), tail = atof(argv[4]);
    int                         rate                           = (argc > 6) ? atoi(argv[6]) : 48000;
    void *                      inst                           = d->cb.create(d);
    tSynthLibSetup              setup                          = {.sampleRate = rate, .maxFrames = 256, .offline = true};
    double                      values[kP2ParamCount];
    char                        name[P2_SOUND_NAME_LENGTH + 1] = "defaults";

    for (uint32_t i = 0; i < kP2ParamCount; i++) {
        values[i] = gP2Params[i].defaultNormalized;
    }

    if ((strcmp(argv[1], "-") != 0) && !p2_patch_load_file(argv[1], values, name)) {
        fprintf(stderr, "not a Pulse 2 sound dump: %s\n", argv[1]);
        return 1;
    }

    for (int a = 7; a < argc; a++) {
        if (strncmp(argv[a], "vel=", 4) == 0) {             // the notes' velocity, 1..127 (default 100)
            velocity = (float)atof(argv[a] + 4) / 127.0f;
            continue;
        }

        if (!apply_override(values, argv[a])) {
            fprintf(stderr, "no parameter for %s\n", argv[a]);
            return 2;
        }
    }

    for (uint32_t i = 0; i < kP2ParamCount; i++) {
        // not Program or Bank: setting them IS a program change, which would load P001 over the sound under test
        if ((i != kP2ParamProgram) && (i != kP2ParamBank)) {
            d->cb.setParam(inst, i, values[i]);
        }
    }

    d->cb.prepare(inst, &setup);
    d->cb.setActive(inst, true);

    size_t  total = (size_t)((0.1 + hold + tail) * rate), on = (size_t)(0.1 * rate), off = on + (size_t)(hold * rate);
    float * mono    = calloc(total, sizeof(float));
    float   left[256], right[256];
    float * outs[2] = {left, right};

    for (size_t at = 0; at < total; at += 256) {
        uint32_t frames = (uint32_t)((total - at) < 256 ? (total - at) : 256);

        for (int n = 0; n < noteCount; n++) {
            size_t nOn  = sequence ? (on + (size_t)(starts[n] * rate)) : on;
            size_t nOff = sequence ? (nOn + (size_t)(lengths[n] * rate)) : off;

            if ((at <= nOn) && (nOn < at + frames)) {
                d->cb.noteOn(inst, 0, (uint8_t)notes[n], velocity, (uint32_t)(nOn - at));
            }

            if ((at <= nOff) && (nOff < at + frames)) {
                d->cb.noteOff(inst, 0, (uint8_t)notes[n], 0.0f, (uint32_t)(nOff - at));
            }
        }

        d->cb.process(inst, NULL, 0, outs, 2, frames, NULL);
        memcpy(mono + at, left, frames * sizeof(float));
    }

    write_wav(argv[5], mono, total, rate);
    printf("%s: \"%s\" note %d, %.2f s\n", argv[5], name, note, (double)total / rate);
    d->cb.destroy(inst);
    free(mono);
    return 0;
}
