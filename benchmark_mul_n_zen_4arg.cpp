#include <cstdint>

#include <gmp.h>

extern "C" {
void mul_n_zen_4arg(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr);
}

#define SUBR(x, y, z) mul_n_zen_4arg(x, y, SIZE, z)
#if SIZE < 4
    #define V 600
#elif SIZE == 4
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
