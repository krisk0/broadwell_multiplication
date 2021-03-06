#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
void mul_4x_zen_5arg(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, SIZE, v, SIZE)
#define BAAD(r, u, v) mul_4x_zen_5arg(r, u, SIZE, v, SIZE)
#define RAND_SEED 20190610

#include "test-internal.h"

int main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
