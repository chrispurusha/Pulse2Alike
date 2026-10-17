// Offline check of src/p2Filter.c against the instrument's measured filter (findings 2026-10-17).
// Build and run: tools/do-filtercheck
#include <math.h>
#include <stdbool.h>
#include <stdio.h>

#include "p2Filter.h"

#define FS         (192000.0)
#define SECONDS    (1.0)

static int failures;

static void check(const char * what, double got, double want, double tolerance) {
    bool ok = fabs(got - want) <= tolerance;

    printf("%-44s %10.2f (want %.2f +- %.2f) %s\n", what, got, want, tolerance, ok ? "" : "FAIL");
    failures += ok ? 0 : 1;
}

// Self-oscillation: no input but a tiny kick, then count zero crossings over the last half second.
static void self_oscillation(double cutoff, double want_hz) {
    tP2Filter f;
    int       n = (int)(FS * SECONDS), crossings = 0;
    double    prev = 0.0, first = -1.0, last = 0.0, peak = 0.0;

    p2_filter_init(&f, FS);
    p2_filter_set(&f, cutoff, 127.0, eP2FilterLp24);

    for (int i = 0; i < n; i++) {
        double y = p2_filter_process(&f, (i == 0) ? 0.01 : 0.0);

        if ((i > n / 2) && (prev < 0.0) && (y >= 0.0)) {
            double t = (i - 1) + (-prev / (y - prev));

            if (first < 0.0) {
                first = t;
            } else {
                crossings++;
                last = t;
            }
        }

        if (i > n / 2) {
            peak = fmax(peak, fabs(y));
        }
        prev = y;
    }

    char what[64];

    snprintf(what, sizeof(what), "self-oscillation Hz at cutoff %.0f", cutoff);
    check(what, (crossings > 0) ? (crossings * FS / (last - first)) : 0.0, want_hz, want_hz * 0.003);
    printf("    amplitude %.3f\n", peak);
}

// Small-signal gain of a sine through the filter, in dB.
static double gain_db(double cutoff, double resonance, tP2FilterMode mode, double hz) {
    tP2Filter f;
    int       n = (int)(FS * 0.5);
    double    in = 0.0, out = 0.0, amp = 0.001;

    p2_filter_init(&f, FS);
    p2_filter_set(&f, cutoff, resonance, mode);

    for (int i = 0; i < n; i++) {
        double x = amp * sin(2.0 * M_PI * hz * i / FS);
        double y = p2_filter_process(&f, x);

        if (i > n / 2) {
            in  += x * x;
            out += y * y;
        }
    }

    return 10.0 * log10(out / in);
}

int main(void) {
    self_oscillation(40.0, 241.9);
    self_oscillation(64.0, 972.0);
    self_oscillation(88.0, 3894.7);

    // measured LP24, resonance 0 (third-octave smoothed takes, findings): bass +4.8 dB, then the slope
    check("LP24 c64 r0 gain at 40 Hz", gain_db(64, 0, eP2FilterLp24, 40.0), 4.9, 0.6);
    check("LP24 c64 r0 gain at 972 Hz (fc)", gain_db(64, 0, eP2FilterLp24, 972.0), -9.2, 1.5);
    check("LP24 c64 r0 gain at 1944 Hz (2fc)", gain_db(64, 0, eP2FilterLp24, 1944.0), -24.9, 2.0);
    check("LP24 c64 r96 bass loss at 40 Hz", gain_db(64, 96, eP2FilterLp24, 40.0), -9.1, 1.0);
    check("LP12 c64 r0 gain at 1944 Hz (2fc)", gain_db(64, 0, eP2FilterLp12, 1944.0), -13.3, 2.0);
    check("BP12 c64 r0 gain at 972 Hz (fc)", gain_db(64, 0, eP2FilterBp12, 972.0), -10.1, 2.0);
    check("HP12 c64 r0 gain at 3888 Hz (4fc)", gain_db(64, 0, eP2FilterHp12, 3888.0), -11.3, 2.0);
    check("HP12 c64 r0 gain at 243 Hz (fc/4)", gain_db(64, 0, eP2FilterHp12, 243.0), -31.0, 6.0);
    printf("%s\n", failures ? "FAILED" : "all passed");
    return failures ? 1 : 0;
}
