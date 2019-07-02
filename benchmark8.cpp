#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#include "automagic/mul8_store_once.h"

uint64_t g_scratch[8];

#define BASECASE(x, y, z) __gmpn_mul_basecase(x, y, 8, z, 8)
#define MUL8(x, y, z) __gmpn_mul(x, y, 8, z, 8)
#define CUSTOM(x, y, z) mul8_broadwell_store_once_wr(x, y, z)
#define SIZE 8
#define VOLUME (1000*1000*100)
#define HELLO
#define GOODBYE

#include "benchmark-internal.c"
