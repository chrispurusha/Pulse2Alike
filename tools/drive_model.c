// The engine's drive curve (src/p2Drive.c) with every constant passed in, for tools/drive_shape.py to fit - built
// by that script into a shared library. p2Drive notes §6.
#include <math.h>

// shape: positive, negative, bias, couplingHz, shelfDirect, shelfHz, hardPos, hardNeg; loss: knee, slope, trim
// (slope 0 = no quiet-input loss)
static double knee_clip(double u, double ceiling, double hard) {
    double x = u / ceiling;

    return ceiling * x / pow(1.0 + pow(fabs(x), hard), 1.0 / hard);
}

// negScale: the negative ceiling's scale at this Drive (p2Drive notes §9; 1 = as the shape)
void drive_run2(const double * x, int n, double rate, const double * shape, double gain, const double * loss, double negScale,
                double * out) {
    double kc = 1.0 - exp(-2.0 * M_PI * shape[3] / rate), ks = 1.0 - exp(-2.0 * M_PI * shape[5] / rate);
    double kd = 1.0 - exp(-2.0 * M_PI * 5.0 / rate);
    double ka = 1.0 - exp(-1.0 / (0.003 * rate)), kr = 1.0 - exp(-1.0 / (0.060 * rate));
    double coupled = 0.0, low = 0.0, dc = 0.0, power = 0.0;

    for (int i = 0; i < n; i++) {
        double v = x[i], p2 = v * v, cf = 1.0;

        power   += ((p2 > power) ? ka : kr) * (p2 - power);

        if (loss[1] > 0.0) {
            double level = (10.0 * log10(fmax(power, 1e-20))) - 3.15;

            cf = pow(10.0, (loss[2] - (loss[1] * fmax(0.0, loss[0] - level))) / 20.0);
        }
        double u = (v * gain) - coupled + (shape[2] * cf);
        double c = (u >= 0.0) ? knee_clip(u, shape[0] * cf, shape[6]) : knee_clip(u, shape[1] * cf * negScale, shape[7]);

        coupled += kc * c;
        low     += ks * (c - low);
        double o = (shape[4] * c) + ((1.0 - shape[4]) * low) - dc;

        dc      += kd * o;
        out[i]   = o;
    }
}

void drive_run(const double * x, int n, double rate, const double * shape, double gain, const double * loss, double * out) {
    drive_run2(x, n, rate, shape, gain, loss, 1.0, out);
}
