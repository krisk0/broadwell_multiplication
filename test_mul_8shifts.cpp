#include <cstdint>

#include <gmp.h>

#ifndef TESTED
    #error TESTED not defined
#endif

#if defined(EXTRA_INCLUDE)
    #include EXTRA_INCLUDE
#endif

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr, mp_size_t, mp_srcptr, mp_size_t);
void TESTED(mp_ptr, mp_srcptr, mp_srcptr);
}

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, SIZE, v, SIZE)
#define BAAD(r, u, v) TESTED(r, u, v)
#define RAND_SEED 20210206

mp_limb_t* g_v;
mp_limb_t __attribute__ ((aligned (16))) g_v_pool[1 + SIZE];
mp_limb_t* g_u;
mp_limb_t __attribute__ ((aligned (16))) g_u_pool[1 + SIZE];
mp_limb_t* g_baad;
mp_limb_t __attribute__ ((aligned (16))) g_baad_pool[1 + 2 * SIZE];

#define V_ALREADY_DEFINED
#define U_ALREADY_DEFINED
#define R_ALREADY_DEFINED
#include "test-internal.h"

int main() {
    for (uint16_t i = 0; i < 8; i++) {
        uint16_t u_ofs = i & 1;
        uint16_t v_ofs = !!(i & 2);
        uint16_t r_ofs = !!(i & 4);
        printf("Testing u/v/r offset %u/%u/%u\n", u_ofs, v_ofs, r_ofs);
        g_v = g_v_pool + v_ofs;
        g_u = g_u_pool + u_ofs;
        g_baad = g_baad_pool + r_ofs;
        do_test();
    }

    printf("Test passed\n");
    return 0;
}
