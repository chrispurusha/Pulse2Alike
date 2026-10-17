/*
 * play - a mono WAV file out of chosen channels of an audio interface, for driving the Pulse 2's EXT IN.
 *
 * Copyright (C) 2026 Chris Turner <chris_purusha@icloud.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
// Notes: Docs/code-notes/play.md - "// notes §k" refers there.

#include <AudioToolbox/AudioToolbox.h>
#include <CoreAudio/CoreAudio.h>
#include <CoreFoundation/CoreFoundation.h>
#include <math.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define MAX_CHANNELS    (64)

static float *        gSamples;
static size_t         gCount;
static _Atomic size_t gPos;
static bool           gPlay[MAX_CHANNELS];

static bool ok(OSStatus status, const char * what) {
    if (status == noErr) {
        return true;
    }
    fprintf(stderr, "error: %s failed (%d)\n", what, (int)status);
    return false;
}

static char * device_name(AudioObjectID device) {
    AudioObjectPropertyAddress address = {kAudioObjectPropertyName, kAudioObjectPropertyScopeGlobal, kAudioObjectPropertyElementMain};
    CFStringRef                name    = NULL;
    UInt32                     size    = sizeof(CFStringRef);   // the property IS a pointer, not the string's bytes

    if (AudioObjectGetPropertyData(device, &address, 0, NULL, &size, &name) != noErr || name == NULL) {
        return NULL;
    }
    CFIndex                    max     = CFStringGetMaximumSizeForEncoding(CFStringGetLength(name), kCFStringEncodingUTF8) + 1;
    char *                     out     = calloc(1, (size_t)max);

    if (out != NULL) {
        CFStringGetCString(name, out, max, kCFStringEncodingUTF8);
    }
    CFRelease(name);
    return out;
}

// Output channel count, summed over the device's output streams. Zero means input-only.
static uint32_t device_output_channels(AudioObjectID device) {
    AudioObjectPropertyAddress address  = {kAudioDevicePropertyStreamConfiguration, kAudioDevicePropertyScopeOutput, kAudioObjectPropertyElementMain};
    UInt32                     size     = 0;

    if (AudioObjectGetPropertyDataSize(device, &address, 0, NULL, &size) != noErr || size == 0) {
        return 0;
    }
    AudioBufferList *          list     = malloc(size);
    uint32_t                   channels = 0;

    if (list != NULL) {
        if (AudioObjectGetPropertyData(device, &address, 0, NULL, &size, list) == noErr) {
            for (UInt32 i = 0; i < list->mNumberBuffers; i++) {
                channels += list->mBuffers[i].mNumberChannels;
            }
        }
        free(list);
    }
    return channels;
}

static double device_rate(AudioObjectID device) {
    AudioObjectPropertyAddress address = {kAudioDevicePropertyNominalSampleRate, kAudioObjectPropertyScopeGlobal, kAudioObjectPropertyElementMain};
    Float64                    rate    = 0.0;
    UInt32                     size    = sizeof(rate);

    if (AudioObjectGetPropertyData(device, &address, 0, NULL, &size, &rate) != noErr) {
        return 0.0;
    }
    return (double)rate;
}

static AudioObjectID * all_devices(uint32_t * countOut) {
    AudioObjectPropertyAddress address = {kAudioHardwarePropertyDevices, kAudioObjectPropertyScopeGlobal, kAudioObjectPropertyElementMain};
    UInt32                     size    = 0;

    *countOut = 0;

    if (AudioObjectGetPropertyDataSize(kAudioObjectSystemObject, &address, 0, NULL, &size) != noErr) {
        return NULL;
    }
    AudioObjectID *            list    = malloc(size);

    if (list == NULL) {
        return NULL;
    }

    if (AudioObjectGetPropertyData(kAudioObjectSystemObject, &address, 0, NULL, &size, list) != noErr) {
        free(list);
        return NULL;
    }
    *countOut = size / (uint32_t)sizeof(AudioObjectID);
    return list;
}

static void list_devices(void) {
    uint32_t        count = 0;
    AudioObjectID * list  = all_devices(&count);

    printf("output devices:\n");

    for (uint32_t i = 0; i < count; i++) {
        uint32_t channels = device_output_channels(list[i]);

        if (channels > 0) {
            char * name = device_name(list[i]);

            printf("  %-40s %2u ch  %.0f Hz\n", (name != NULL) ? name : "?", channels, device_rate(list[i]));
            free(name);
        }
    }

    free(list);
}

// The first device with outputs whose name contains `wanted`.
static AudioObjectID find_device(const char * wanted, uint32_t * channelsOut) {
    uint32_t        count = 0;
    AudioObjectID * list  = all_devices(&count);
    AudioObjectID   found = kAudioObjectUnknown;

    for (uint32_t i = 0; (i < count) && (found == kAudioObjectUnknown); i++) {
        uint32_t channels = device_output_channels(list[i]);
        char *   name     = device_name(list[i]);

        if ((channels > 0) && (name != NULL) && (strstr(name, wanted) != NULL)) {
            found        = list[i];
            *channelsOut = channels;
            fprintf(stderr, "device \"%s\": %u output channels at %.0f Hz\n", name, channels, device_rate(list[i]));
        }
        free(name);
    }

    free(list);
    return found;
}

static OSStatus render(void * ref, AudioUnitRenderActionFlags * flags, const AudioTimeStamp * ts,
                       UInt32 bus, UInt32 frames, AudioBufferList * io) {
    (void)ref;
    (void)flags;
    (void)ts;
    (void)bus;
    size_t pos = atomic_load_explicit(&gPos, memory_order_relaxed);

    for (UInt32 f = 0; f < frames; f++) {
        float x = (pos < gCount) ? gSamples[pos] : 0.0f;

        pos++;

        for (UInt32 b = 0; b < io->mNumberBuffers; b++) {
            ((float *)io->mBuffers[b].mData)[f] = ((b < MAX_CHANNELS) && gPlay[b]) ? x : 0.0f;
        }
    }

    atomic_store_explicit(&gPos, pos, memory_order_relaxed);
    return noErr;
}

// notes §1
static bool load_wav(const char * path, double * rateOut) {
    FILE *   f    = fopen(path, "rb");
    uint8_t  hdr[12];
    uint16_t format = 0, channels = 0, bits = 0;
    uint32_t rate = 0;

    if ((f == NULL) || (fread(hdr, 1, 12, f) != 12) || (memcmp(hdr, "RIFF", 4) != 0) || (memcmp(hdr + 8, "WAVE", 4) != 0)) {
        fprintf(stderr, "error: %s is not a WAV file\n", path);
        return false;
    }

    for ( ; ;) {
        uint8_t  chunk[8];
        uint32_t size;

        if (fread(chunk, 1, 8, f) != 8) {
            fprintf(stderr, "error: no data chunk in %s\n", path);
            return false;
        }
        size = (uint32_t)chunk[4] | ((uint32_t)chunk[5] << 8) | ((uint32_t)chunk[6] << 16) | ((uint32_t)chunk[7] << 24);

        if (memcmp(chunk, "fmt ", 4) == 0) {
            uint8_t fmt[40] = {0};

            if ((size > sizeof(fmt)) || (fread(fmt, 1, size, f) != size)) {
                return false;
            }
            format   = (uint16_t)(fmt[0] | (fmt[1] << 8));
            channels = (uint16_t)(fmt[2] | (fmt[3] << 8));
            rate     = (uint32_t)fmt[4] | ((uint32_t)fmt[5] << 8) | ((uint32_t)fmt[6] << 16) | ((uint32_t)fmt[7] << 24);
            bits     = (uint16_t)(fmt[14] | (fmt[15] << 8));
        } else if (memcmp(chunk, "data", 4) == 0) {
            if ((channels != 1) || !(((format == 1) && (bits == 32)) || ((format == 3) && (bits == 32)))) {
                fprintf(stderr, "error: %s must be mono, 32-bit integer or float\n", path);
                return false;
            }
            gCount   = size / 4;
            gSamples = malloc(gCount * sizeof(float));

            if ((gSamples == NULL) || (fread(gSamples, 4, gCount, f) != gCount)) {
                return false;
            }

            if (format == 1) {
                for (size_t i = 0; i < gCount; i++) {
                    int32_t v;

                    memcpy(&v, &gSamples[i], 4);
                    gSamples[i] = (float)((double)v / 2147483648.0);
                }
            }
            *rateOut = rate;
            fclose(f);
            return true;
        } else {
            fseek(f, (long)(size + (size & 1)), SEEK_CUR);
        }
    }
}

static void usage(const char * self) {
    fprintf(stderr,
            "usage: %s --list\n"
            "       %s --device <name> --channels 5[,6...] --file <mono.wav>\n"
            "  plays the file once at its own rate, which must be the device's; other channels are silent\n", self, self);
}

int main(int argc, char ** argv) {
    const char * wanted = NULL;
    const char * file   = NULL;
    bool         anyOn  = false;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--list") == 0) {
            list_devices();
            return 0;
        } else if ((strcmp(argv[i], "--device") == 0) && ((i + 1) < argc)) {
            wanted = argv[++i];
        } else if ((strcmp(argv[i], "--file") == 0) && ((i + 1) < argc)) {
            file = argv[++i];
        } else if ((strcmp(argv[i], "--channels") == 0) && ((i + 1) < argc)) {
            for (char * tok = strtok(argv[++i], ","); tok != NULL; tok = strtok(NULL, ",")) {
                unsigned long c = strtoul(tok, NULL, 10);

                if (c < MAX_CHANNELS) {
                    gPlay[c] = true;
                    anyOn    = true;
                }
            }
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if ((wanted == NULL) || (file == NULL) || (anyOn == false)) {
        usage(argv[0]);
        return 2;
    }
    double                      fileRate = 0.0;

    if (!load_wav(file, &fileRate)) {
        return 1;
    }

    for (size_t i = 0; i < gCount; i++) {
        if (fabsf(gSamples[i]) > 1.0f) {
            fprintf(stderr, "error: sample %zu is above full scale\n", i);
            return 2;
        }
    }

    uint32_t                    channels = 0;
    AudioObjectID               device   = find_device(wanted, &channels);

    if (device == kAudioObjectUnknown) {
        fprintf(stderr, "error: no output device matching \"%s\" (try --list)\n", wanted);
        return 1;
    }
    double                      rate     = device_rate(device);

    if (rate != fileRate) {
        fprintf(stderr, "error: the file is %.0f Hz and the device runs at %.0f Hz\n", fileRate, rate);
        return 1;
    }
    AudioComponentDescription   desc     = {kAudioUnitType_Output, kAudioUnitSubType_HALOutput, kAudioUnitManufacturer_Apple, 0, 0};
    AudioComponent              comp     = AudioComponentFindNext(NULL, &desc);
    AudioUnit                   unit     = NULL;

    if ((comp == NULL) || !ok(AudioComponentInstanceNew(comp, &unit), "AudioComponentInstanceNew")) {
        return 1;
    }

    if (!ok(AudioUnitSetProperty(unit, kAudioOutputUnitProperty_CurrentDevice, kAudioUnitScope_Global, 0, &device, sizeof(device)), "set device")) {
        return 1;
    }
    AudioStreamBasicDescription format   = {0};

    format.mSampleRate       = rate;
    format.mFormatID         = kAudioFormatLinearPCM;
    format.mFormatFlags      = kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked | kAudioFormatFlagIsNonInterleaved;
    format.mBytesPerPacket   = sizeof(float);
    format.mFramesPerPacket  = 1;
    format.mBytesPerFrame    = sizeof(float);
    format.mChannelsPerFrame = channels;
    format.mBitsPerChannel   = 32;

    if (!ok(AudioUnitSetProperty(unit, kAudioUnitProperty_StreamFormat, kAudioUnitScope_Input, 0, &format, sizeof(format)), "set format")) {
        return 1;
    }
    AURenderCallbackStruct      callback = {render, NULL};

    if (  !ok(AudioUnitSetProperty(unit, kAudioUnitProperty_SetRenderCallback, kAudioUnitScope_Input, 0, &callback, sizeof(callback)), "set callback")
       || !ok(AudioUnitInitialize(unit), "AudioUnitInitialize")
       || !ok(AudioOutputUnitStart(unit), "AudioOutputUnitStart")) {
        return 1;
    }

    while (atomic_load(&gPos) < gCount + (size_t)(rate * 0.1)) {
        usleep(20000);
    }
    AudioOutputUnitStop(unit);
    AudioUnitUninitialize(unit);
    AudioComponentInstanceDispose(unit);
    printf("played %.2f s\n", (double)gCount / rate);
    return 0;
}
