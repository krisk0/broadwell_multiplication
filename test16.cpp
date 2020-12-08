#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#include "toom22_generic.h"

uint64_t g_scratch[16];

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, 16, v, 16)
#define BAAD(r, u, v) toom22_mul16_broadwell(r, g_scratch, u, v)
#define SIZE 16
#define RAND_SEED 20190619

#include "test-internal.h"

int main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
