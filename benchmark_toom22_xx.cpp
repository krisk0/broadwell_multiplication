/*
Benchmark subroutine toom22_xx_broadwell() against mpn_mul_n() and __gmpn_toom22_mul().
 
Command-line parameters: size count/1000
 where size is operand size in limbs, count is count of multiplications to do
*/
#include <stdlib.h>

#include "toom22_generic.h"
#include "random-number.h"

extern "C" {
void __gmpn_toom22_mul(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t, mp_ptr);
}

#define MAX_N 128
#define RAND_SEED 20190722
#define INT mp_limb_t

INT* g_scratch;
INT* g_a;
INT g_size;
INT g_volume;
INT g_page_size;
INT g_page_mask;
INT g_page_unmask;

#if SUBR == 3
    #define CALL_SUBR(r, a, b) __gmpn_mul_basecase(r, a, g_size, b, g_size)
#elif SUBR == 2
    #define CALL_SUBR(r, a, b) toom22_xx_broadwell(r, g_scratch, a, b, (uint16_t)g_size)
#elif SUBR == 1
    #define CALL_SUBR(r, a, b) __gmpn_toom22_mul(r, a, g_size, b, g_size, g_scratch)
    // gmp-impl.h defines itch size like this
    #define ITCH_SIZE 2 * (MAX_N + GMP_NUMB_BITS)
#elif SUBR == 0
    #define CALL_SUBR(r, a, b) mpn_mul_n(r, a, b, g_size)
#endif

#if !defined(ITCH_SIZE)
static constexpr auto ITCH_SIZE = itch::toom22_t_max_over_range<TOOM_2T_BOUND,
        MAX_N>();
#endif

void
do_benchmark() {
    bordeless_alloc(INT, pool_0, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc(INT, pool_1, g_page_size, g_page_mask, g_page_unmask);

    random_number<INT>(g_a, g_size);
    random_number<INT>(pool_0, g_size);
    random_number<INT>(pool_1, g_size);

    auto mask = (g_page_size / sizeof(INT) / 2) - 1;
    INT i = 0, j = g_size;
    auto volume_half = g_volume / 2;

    auto t = __rdtsc();
    for(INT k = volume_half; k--;) {
        CALL_SUBR(pool_0 + j, pool_1 + i, g_a);
        CALL_SUBR(pool_1 + j, g_a, pool_0 + i);
        i = (i + 1) & mask;
        j = (j + g_size * 2) & mask;
    }
    t = __rdtsc() - t;

    auto cycles = t / g_volume;
    j = (j + mask - 1 - g_size * 2) & mask;
    printf("spent %lld   ticks %lld   result %lX\n", t, cycles, pool_1[j]);
}

int
main(int, char** p) {
    srand(RAND_SEED);
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    g_page_size = 1 + g_page_mask;
    bordeless_alloc_nodefine(INT, g_scratch, ITCH_SIZE * sizeof(INT), g_page_mask,
            g_page_unmask);
    bordeless_alloc_nodefine(INT, g_a, MAX_N * sizeof(INT), g_page_mask, g_page_unmask);
    g_size = atol(p[1]);
    g_volume = 1000 * atol(p[2]);

    do_benchmark();

    return 0;
}
