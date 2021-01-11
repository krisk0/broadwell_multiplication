#include <cstdint>

#include <gmp.h>

// Run do_test() twice, with different alignments of 3rd argument

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr, mp_size_t, mp_srcptr, mp_size_t);
void TESTED(mp_ptr, mp_srcptr);
#define BAAD(r, u, v) wrapper(r, u, v)
}

void
wrapper(mp_ptr r, mp_srcptr a, mp_srcptr b) {
    if (a < b) {
        TESTED(r, a);
    } else {
        TESTED(r, b);
    }
}

#ifndef SIZE
    #define SIZE 8
#endif
#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, SIZE, v, SIZE)
#define RAND_SEED 20190610

mp_limb_t g_u[2 * SIZE];
mp_limb_t* g_v = g_u + SIZE;

#define V_ALREADY_DEFINED
#define U_ALREADY_DEFINED
#include "test-internal.h"

int
main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
