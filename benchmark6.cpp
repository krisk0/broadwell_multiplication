#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#include "automagic/mul6.h"
#include "automagic/mul6_zen.h"

#define BASECASE(x, y, z) __gmpn_mul_basecase(x, y, 6, z, 6)
#define MUL6(x, y, z) __gmpn_mul(x, y, 6, z, 6)
#define C_BROADWELL(x, y, z) mul6_broadwell_wr(x, y, z)
#define C_ZEN(x, y, z) mul6_zen_wr(x, y, z)
#define SIZE 6
#define VOLUME (1000*1000*150)
#define HELLO
#define GOODBYE

#include "benchmark-internal.c"
