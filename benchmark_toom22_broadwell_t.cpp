// Benchmark subroutine toom22_broadwell_t<>() against GMP basecase/official subroutine

#if CUSTOM == 1
    #define CALL(rp, ap, bp, n) toom22_broadwell_t<n>(rp, g_scratch, ap, bp)
#endif
#if CUSTOM == 0
    #define CALL(rp, ap, bp, n) call_gmp_t<n>(rp, ap, bp)
#endif

#include "toom22_generic.h"

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
}

#define INT mp_limb_t
INT* g_scratch;
INT g_page_size;
INT g_page_mask;
INT g_page_unmask;

template <uint16_t N>
void
call_gmp_t(mp_ptr rp, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N < 28) {
        // for small N call mpn_mul_basecase() directly -- this is what mpn_mul_n() does
        __gmpn_mul_basecase(rp, ap, N, bp, N);
    } else {
        // let mpn_mul_n() select subroutine to call and scratch
        mpn_mul_n(rp, ap, bp, (INT)N);
    }
}

#include "benchmark-dynamic.h"

#define RAND_SEED 20190729
#define MIN_N 12
/*
for N=12..127, max itch size is 348, reached at 127.

itch size is output by scratch_size.py 
*/
#define MAX_N 127
#define ITCH_SIZE 348

int
main(int c, char** p) {
    srand(RAND_SEED);
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    g_page_size = 1 + g_page_mask;
    bordeless_alloc_nodefine(INT, g_scratch, ITCH_SIZE * sizeof(INT), g_page_mask,
            g_page_unmask);
    INT volume = atol(p[1]);
    
    benchmark_dynamic::test<MIN_N, MAX_N>(volume);

    return 0;
}
