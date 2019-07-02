#include "automagic/toom22_mul_16.h"

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

uint64_t g_scratch[16];

#define SIZE 16
#define BASECASE(x, y, z) __gmpn_mul_basecase(x, y, SIZE, z, SIZE)
#define MUL16(x, y, z) __gmpn_mul(x, y, SIZE, z, SIZE)
#define TOOM(x, y, z) toom22_mul16_broadwell(x, g_scratch, y, z)
#define VOLUME (1000*1000*100)

// __gmpn_mul_basecase: 409
// __gmpn_mul: 436
// toom22_mul16_broadwell: 348

#if TIME_INTERPOLATE
uint64_t
count_interpolate_time(int w) {
    auto result = ((double)g_time_interpolate[w]) / g_count_interpolate[w];
    return (uint64_t)result;
}

void
show_interpolate_time() {
    uint64_t t[2];
    for(int i = 0; i < 2; i++) {
        t[i] = count_interpolate_time(i);
    }
    printf("Average interpolation time: %lu / %lu\n", t[0], t[1]);
}
#define HELLO memset(g_time_interpolate, 0, 2 * sizeof(uint64_t)); \
        memset(g_count_interpolate, 0, 2 * sizeof(uint64_t));
#define GOODBYE show_interpolate_time();
#else
#define HELLO
#define GOODBYE
#endif

#include "benchmark-internal.c"
