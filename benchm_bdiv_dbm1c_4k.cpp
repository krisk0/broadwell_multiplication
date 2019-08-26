/*
benchmark mpn_bdiv_dbm1c_4k_func() against __gmpn_bdiv_dbm1c()

result: 3.2 .. 3.7 per limb

mulx variant appears to be slightly faster (difference is very little)
*/

#include <cstdint>
#include <time.h>

#include <gmp.h>

#include "automagic/bdiv_dbm1c_4k.h"

#define INT mp_limb_t

extern "C" {
INT __gmpn_bdiv_dbm1c(mp_ptr, mp_srcptr, mp_size_t, INT, INT);
}

#include "bordeless-alloc.h"
#include "random-number.h"

INT g_page_size;
INT g_page_mask;
INT g_page_unmask;
INT g_volume;
INT* g_pool_0;
INT* g_pool_1;
#define RAND_SEED 20190731

template <uint16_t N, uint8_t CUSTOM>
void
call_subroutine(mp_ptr rp, mp_srcptr up) {
    if constexpr (CUSTOM) {
        mpn_bdiv_dbm1c_4k_func(rp, up, N, GMP_NUMB_MASK / 3);
    } else {
        (void)__gmpn_bdiv_dbm1c(rp, up, N, GMP_NUMB_MASK / 3, 0);
    }
}

template <uint16_t N, uint8_t CUSTOM>
INT
do_benchmark(const char* id, uint16_t next_n) {
    srand(RAND_SEED + N);
    random_number<INT>(g_pool_0 + 0, g_page_size / sizeof(INT));
    auto mask = (g_page_size / sizeof(INT) / 2) - 1;

    auto seconds = time(NULL);
    auto ticks = __rdtsc();
    INT i = 0;
    for (INT k = g_volume; k--;) {
        call_subroutine<N, CUSTOM>(g_pool_1 + i, g_pool_0 + i);
        i = (i + 1) & mask;
    }
    ticks = __rdtsc() - ticks;
    seconds = time(NULL) - seconds;
    auto cycles = double(ticks) / g_volume;

    printf("size %u   subr %s()   seconds %ld  ticks per call %f\n", N, id, seconds,
            cycles);
    INT new_volume;
    if (seconds) {
        // make it about 4 seconds next time
        new_volume = INT(double(4) / seconds * N / next_n * g_volume);
    } else {
        new_volume = 10 * g_volume;
    }
    return new_volume;
}

template <uint16_t N>
void
benchmark(uint16_t next_n) {
    printf("N=%u volume=%ld\n", N, g_volume);
    (void)do_benchmark<N, 0>("gmpn_bdiv_dbm1c", next_n);
    g_volume = do_benchmark<N, 1>("custom mpn_bdiv_dbm1c_4k", next_n);
}

int
main(int c, char** p) {
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    g_page_size = 1 + g_page_mask;
    bordeless_alloc_nodefine(INT, g_pool_0, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc_nodefine(INT, g_pool_1, g_page_size, g_page_mask, g_page_unmask);
    g_volume = 1000 * 1000 * 1000;

    benchmark<4>(8);
    benchmark<8>(12);
    benchmark<12>(16);
    benchmark<16>(24);
    benchmark<24>(60);
    benchmark<60>(60);
}
