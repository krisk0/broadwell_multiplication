#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#include "automagic/mpn_le_4.h"
#include "automagic/mul4_broadwell.h"
#include "automagic/mpn_sub_4.h"
#include "automagic/subtract_lesser_from_bigger_4.h"
#include "automagic/add_sub_8.h"
#include "automagic/sum_subtract_8.h"
#include "automagic/toom22_mul.h"

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, 8, v, 8)
#define BAAD(r, u, v) toom22_mul8_broadwell(r, g_scratch, u, v)
#define SIZE 8
#define RAND_SEED 20190610

INT g_scratch[8];

#include "test-internal.h"

int main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
