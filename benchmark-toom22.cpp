#include "automagic/toom22_mul_16.h"
#include "automagic/toom22_generic_aux.h"
#include "toom22_generic.h"

extern "C" {
void __gmpn_toom22_mul(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t, mp_ptr);
}

// 256 == mpn_toom22_mul_itch(64, 64)
uint64_t g_scratch[256]; // TODO: use posix_memalign() to ensure no page boundaries

#define MULN(x, y, z) __gmpn_mul(x, y, SIZE, z, SIZE)
#define TOOM_GMP(x, y, z) __gmpn_toom22_mul(x, y, SIZE, z, SIZE, g_scratch + 0)
#define TOOM_CUSTOM(x, y, z) toom22_deg2_broadwell(x, g_scratch + 0, y, z, SIZE)
#define VOLUME (1000*1000*20)

#define HELLO
#define GOODBYE

#include "benchmark-internal.c"
