#define TOOM22_2X_BROADWELL_BENCHMARK SIZE

#include <cstdint>

#include "toom22_generic.h"

#if !defined(VOLUME)
    #if SIZE < 50
        #define VOLUME (1000*1000*20)
    #else
        #define VOLUME (1000*1000*10)
    #endif
#endif

uint64_t g_scratch[itch::toom22_forced_t<22>() * sizeof(uint64_t)];

void
SUBR(mp_ptr x, mp_srcptr y, mp_srcptr z) {
    force_call_toom22_broadwell<SIZE>(x, g_scratch + 0, y, z);
}

#define HELLO g_t_subt = g_t_mult = g_t_intt = 0;

#define GOODBYE \
    {                                                                             \
        auto s = g_t_subt / VOLUME;                                               \
        auto m = g_t_mult / VOLUME;                                               \
        auto t = g_t_intt / VOLUME;                                               \
        printf("subtract,multiply,interpolate time = %lld,%lld,%lld\n", s, m, t); \
    }

#include "benchmark-internal.c"
