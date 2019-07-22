/*
Benchmark subroutine toom22_xx_broadwell() against mpn_mul_n() and __gmpn_toom22_mul()
*/
#include <malloc.h>
#include <stdlib.h>
#include <x86intrin.h>
#include <unistd.h>

#include "toom22_generic.h"
#include "random-number.h"

extern "C" {
void __gmpn_toom22_mul(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t, mp_ptr);
}

#define MAX_N 128
#define RAND_SEED 20190722
#define INT mp_limb_t

INT* g_scratch;
INT g_a[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];
INT g_size;
INT g_volume;
INT g_page_size;
 
#if SUBR == 2
    #define CALL_SUBR(r, a, b) toom22_xx_broadwell(r, g_scratch, a, b, (uint16_t)g_size)
#elif SUBR == 1
    #define CALL_SUBR(r, a, b) __gmpn_toom22_mul(r, a, g_size, b, g_size, g_scratch)
#else
    #define CALL_SUBR(r, a, b) mpn_mul_n(r, a, b, g_size)
#endif
 
#if SUBR != CUSTOM
    // gmp-impl.h defines itch size like this 
    #define ITCH_SIZE     2 * (MAX_N + GMP_NUMB_BITS)
#else
    #define ITCH_SIZE     toom22_generic_itch(MAX_N)
#endif

void
do_benchmark() {
    auto pool_0 = (INT*)memalign(g_page_size, g_page_size);
    auto pool_1 = (INT*)memalign(g_page_size, g_page_size);

    random_number<INT>(g_a + 0, g_size);
    random_number<INT>(pool_0, g_size);
    random_number<INT>(pool_1, g_size);
    
    auto mask = (g_page_size / sizeof(INT) / 2) - 1;
    INT i = 0, j = g_size;
    auto volume_half = g_volume / 2;
    auto t = __rdtsc();
    for(INT k = volume_half; k--; ) {
        CALL_SUBR(pool_0 + j, pool_1 + i, g_a + 0);
        CALL_SUBR(pool_1 + j, g_a + 0, pool_0 + i);
        i = (i + 1) & mask;
        j = (j + g_size * 2) & mask;
    }

    t = __rdtsc() - t;
    auto cycles = t / g_volume;
    j = (j + mask - 1 - g_size * 2) & mask;
    printf("spent %lld   ticks %lld   result %lX\n", t, cycles, pool_1[j]);
    
    /*
    Not calling free(). Memory leak
    free(pool_1);
    free(pool_0);
    */
}

int
main(int c, char** v) {
    srand(RAND_SEED);
    g_page_size = sysconf(_SC_PAGE_SIZE);
    g_scratch = (INT*)memalign(g_page_size, sizeof(INT) * (ITCH_SIZE));

    g_size = atol(v[1]);
    g_volume = 1000 * atol(v[2]);
    do_benchmark();

    /*
    Not calling free(). Memory leak
    free(g_scratch);
    */
    
    return 0;
}
