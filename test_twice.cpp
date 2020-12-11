#include <cstdint>

#include <gmp.h>

// Run do_test() twice, with different alignments of 3rd argument

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr, mp_size_t, mp_srcptr, mp_size_t);
void TESTED(mp_ptr, mp_srcptr, mp_srcptr);
#define BAAD(r, u, v) TESTED(r, u, v)
}

#ifndef SIZE
    #define SIZE 8
#endif
#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, SIZE, v, SIZE)
#define RAND_SEED 20190610

mp_limb_t* g_v;
mp_limb_t g_v_pool[1 + SIZE];

#define V_ALREADY_DEFINED
#include "test-internal.h"

int
main() {
    g_v = g_v_pool + 0;
    //printf("alignment %ld\n", ((INT)g_v) & 0xF);
    do_test();
    g_v += 1;
    //printf("alignment %ld\n", ((INT)g_v) & 0xF);
    do_test();

    printf("Test passed\n");
    return 0;
}
