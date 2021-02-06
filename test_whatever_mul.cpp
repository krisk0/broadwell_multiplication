#include <cstdint>

#include <gmp.h>

#include "toom22_generic.h"

#if defined(EXTRA_INCLUDE)
    #include EXTRA_INCLUDE
#endif

#ifndef TESTED
    #error TESTED not defined
#endif

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr, mp_size_t, mp_srcptr, mp_size_t);
void TESTED(mp_ptr, mp_srcptr, mp_srcptr);
}

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, SIZE, v, SIZE)
#define BAAD(r, u, v) TESTED(r, u, v)
#define RAND_SEED 20190619

#include "test-internal.h"

int main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
