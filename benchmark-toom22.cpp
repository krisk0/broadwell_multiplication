#include "toom22_generic.h"

extern "C" {
void __gmpn_toom22_mul(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t, mp_ptr);
}

#define MULN(x, y, z) __gmpn_mul(x, y, SIZE, z, SIZE)
#define TOOM_GMP(x, y, z) __gmpn_toom22_mul(x, y, SIZE, z, SIZE, scratch + 0)
#define TOOM_DEG2(x, y, z) toom22_deg2_broadwell(x, scratch + 0, y, z, SIZE)
#define TOOM_WRAP(x, y, z) toom22_xx_broadwell(x, scratch + 0, y, z, SIZE)
#define TOOM_DEG2_T(x, y, z) toom22_deg2_broadwell_t<SIZE>(x, scratch + 0, y, z)
#if SIZE > 8
    #if 0 && (SIZE & 1)
        #define TOOM_T(x, y, z) toom22_1x_n_minus<SIZE>(x, scratch + 0, y, z)
    #else
        #define TOOM_T(x, y, z) \
            force_call_toom22_broadwell<SIZE>(x, scratch + 0, y, z)
    #endif
#else
    #define TOOM_T(x, y, z) mul_basecase_t<SIZE>(x, y, z)
#endif
#if !defined(VOLUME)
    #if SIZE < 50
        #if SIZE < 8
            #define VOLUME (1000*1000*150)
        #elif SIZE == 8
            #define VOLUME (1000*1000*100)
        #else
            #define VOLUME (1000*1000*20)
        #endif
    #else
        #define VOLUME (1000*1000*10)
    #endif
#endif

#ifndef SCRATCH_TYPE
    #error SCRATCH_TYPE not defined
#endif

constexpr auto g_itch = itch::toom22_forced_t<SIZE>() * sizeof(mp_limb_t);
#if SCRATCH_TYPE == 0
    // scratch not needed in benchmark-internal
    #define HELLO /**/
#elif SCRATCH_TYPE == 1
    // GMP mul_n.c does it like that
    #define mpn_toom22_mul_itch(an, bn) (2 * ((an) + GMP_NUMB_BITS))
    #define HELLO INT scratch[mpn_toom22_mul_itch(SIZE, SIZE)];
#elif SCRATCH_TYPE == 2
    #define HELLO bordeless_alloc(INT, scratch, g_itch, g_page_mask, g_page_unmask);
#elif
    #error bad SCRATCH_TYPE
#endif

#define GOODBYE

#include "benchmark-internal.c"
