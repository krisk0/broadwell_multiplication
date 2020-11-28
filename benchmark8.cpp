#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
void mul8_zen(mp_ptr, mp_srcptr, mp_srcptr);
void mul8x2_zen(mp_ptr, mp_srcptr, mp_srcptr);
}

#if (!ZEN) && (!_8x2)
    #include "automagic/mul8_store_once.h"
#endif

#ifndef SIZE
    #define SIZE 8
#endif
#define BASECASE(x, y, z) __gmpn_mul_basecase(x, y, SIZE, z, SIZE)
#define MUL8(x, y, z) __gmpn_mul(x, y, SIZE, z, SIZE)
#define CUSTOM(x, y, z) mul8_broadwell_store_once_wr(x, y, z)
#ifndef VOLUME
    #if SIZE < 8
        #define VOLUME (1000*1000*150)
    #else
        #define VOLUME (1000*1000*100)
    #endif
#endif
#define HELLO
#define GOODBYE

#if ZEN==1 && SIZE == 8
    #define SUBR(x, y, z) mul8_zen(x, y, z)
#endif

#if _8x2
    #define SUBR(x, y, z) mul8x2_zen(x, y, z)
#endif

#include "benchmark-internal.c"
