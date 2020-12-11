#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
void mul8_zen(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_broadwell_125(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_skylake(mp_ptr, mp_srcptr, mp_srcptr);
void mul8x2_zen(mp_ptr, mp_srcptr, mp_srcptr);
#if defined(TESTED)
    void TESTED(mp_ptr, mp_srcptr, mp_srcptr);
    #define SUBR(x, y, z) TESTED(x, y, z)
#endif
}

#ifndef SIZE
    #define SIZE 8
#endif
#define BASECASE(x, y, z) __gmpn_mul_basecase(x, y, SIZE, z, SIZE)
#define MUL8(x, y, z) __gmpn_mul(x, y, SIZE, z, SIZE)
#define CUSTOM(x, y, z) mul8_broadwell_store_once_wr(x, y, z)
#define BROADWELL_125(x, y, z) mul8_broadwell_125(x, y, z)
#ifndef VOLUME
    #if SIZE < 8
        #define VOLUME (1000*1000*150)
    #else
        #define VOLUME (1000*1000*100)
    #endif
#endif
#define HELLO
#define GOODBYE

#ifndef SUBR
    #if ZEN==1 && SIZE == 8
        #define SUBR(x, y, z) mul8_zen(x, y, z)
    #endif

    #if SKYLAKE==1 && SIZE == 8
        #define SUBR(x, y, z) mul8_skylake(x, y, z)
    #endif

    #if _8x2
        #define SUBR(x, y, z) mul8x2_zen(x, y, z)
    #endif
#endif

#if defined(ALIGN16)
    #include "benchmark-internal-align.c"
#else
    #include "benchmark-internal.c"
#endif
