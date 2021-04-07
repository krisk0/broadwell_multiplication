#define MEASURE_TIME_IN_1X_BROADWELL 1

#include <cstdint>
uint64_t g_0 = SIZE;
long long int g_1 = 0, g_2 = 0;

#include "toom22_generic.h"

#define SUBR(x, y, z) toom22_1x_broadwell(x, scratch + 0, y, z, SIZE)
#if !defined(VOLUME)
    #if SIZE < 50
        #define VOLUME (1000*1000*20)
    #else
        #define VOLUME (1000*1000*10)
    #endif
#endif

constexpr auto g_itch = itch::toom22_t<SIZE>() * sizeof(mp_limb_t);
#define HELLO bordeless_alloc(INT, scratch, g_itch, g_page_mask, g_page_unmask);

#define GOODBYE printf("t0,1 = %lld,%lld\n", g_1 / VOLUME, g_2 / VOLUME);

#include "benchmark-internal.c"
