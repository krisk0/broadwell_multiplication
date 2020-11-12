#include <cstdint>

#include <gmp.h>

extern "C" {
void mul_4x_zen_5arg(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#define SUBR(x, y, z) mul_4x_zen_5arg(x, y, SIZE, z, SIZE)
#if SIZE == 4
    #define V 150
#elif SIZE == 8
    #define V 100
#elif SIZE == 12
    #define V 80
#else
    #define V 60
#endif

#define VOLUME (1000 * 1000 * V)
#define HELLO
#define GOODBYE

#include "benchmark-internal.c"
