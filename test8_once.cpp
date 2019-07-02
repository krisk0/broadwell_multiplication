#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#include "automagic/mul8_store_once.h"

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, 8, v, 8)
#define BAAD(r, u, v) mul8_broadwell_store_once_wr(r, u, v)
#define SIZE 8
#define RAND_SEED 20190610

#include "test-internal.h"

int main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
