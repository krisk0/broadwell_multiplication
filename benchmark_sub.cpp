/*
benchmark subtract subroutines such as mpn_sub_1x() agains mpn_sub_n()

Result: mpn_sub_4k_inplace() and mpn_sub_4k() is slightly faster than gmp_mul_n, other custom
 subroutines are slower
*/

#include <cstdint>

#include <gmp.h>

#include "bordeless-alloc.h"
#include "random-number.h"

#include "automagic/mpn_sub_1x.h"
#include "automagic/mpn_sub_inplace.h"
#include "automagic/mpn_sub_4k.h"
#include "automagic/mpn_sub_4k_inplace.h"

#define INT mp_limb_t
INT g_page_size;
INT g_page_mask;
INT g_page_unmask;
INT* g_pool_0;
INT* g_pool_1;
#define RAND_SEED 20190725

extern "C" {
INT __gmpn_bdiv_dbm1c(mp_ptr, mp_srcptr, mp_size_t, INT, INT);
}

namespace _1x {

constexpr INT VOLUME = 1000*1000*800;

template <uint16_t WHAT, uint16_t SIZE>
void
subtr(mp_ptr u, mp_ptr v) {
    auto t = u + SIZE;
    INT size = SIZE;
    if constexpr (WHAT == 0) {
        mpn_sub_n(t, u, v, size);
    } 
    if constexpr (WHAT == 1) {
        mpn_sub_1x(t, u, v, size);
    }
    if constexpr (WHAT == 2) {
        mpn_sub_n(u, v, u, size);
    }
    if constexpr (WHAT == 3) {
        mpn_sub_inplace(u, v, size);
    }
    if constexpr (WHAT == 4) {
        uint16_t loop_count = (SIZE >> 2) - 1;
        uint8_t carry;
        mpn_sub_4k_inplace(carry, u, v, loop_count);
    }
    if constexpr (WHAT == 5) {
        uint16_t loop_count = (SIZE >> 2) - 1;
        mpn_sub_4k(t, u, v, loop_count);
    }
    if constexpr (WHAT == 6) {
        (void)__gmpn_bdiv_dbm1c(u, v, SIZE, GMP_NUMB_MASK / 3, 0);
    }
    if constexpr (WHAT == 7) {
        (void)mpn_lshift(u, v, SIZE, 1);
    }
}

template <uint16_t WHAT, uint16_t SIZE>
void benchmark(const char* id) {
    random_number<INT>(g_pool_0, SIZE);
    random_number<INT>(g_pool_1, SIZE);
    auto mask = (g_page_size / sizeof(INT) / 2) - 1;
    
    INT i = 0, j = 0;
    auto t = __rdtsc();
    for(unsigned k = VOLUME / 2; k--;) {
        subtr<WHAT, SIZE>(g_pool_0 + j, g_pool_1 + i);
        subtr<WHAT, SIZE>(g_pool_1 + j, g_pool_0 + i);
        i = (i + 1) & mask;
        j = (j + SIZE * 2) & mask;
    }
    t = __rdtsc() - t;
    auto cycles = double(t) / VOLUME;
    printf("%s: spent %lld   ticks %f\n", id, t, cycles);
}

} // end namespace _1x

int
main(int c, char** p) {
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    g_page_size = 1 + g_page_mask;
    srand(RAND_SEED);
    bordeless_alloc_nodefine(INT, g_pool_0, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc_nodefine(INT, g_pool_1, g_page_size, g_page_mask, g_page_unmask);
    
    _1x::benchmark<0, 7>("mpn_sub_n 7");
    _1x::benchmark<1, 7>("mpn_sub_1x 7");
    _1x::benchmark<2, 7>("mpn_sub_n inplace 7");
    _1x::benchmark<3, 7>("mpn_sub_inplace 7");
    _1x::benchmark<2, 8>("mpn_sub_n inplace 8");
    _1x::benchmark<4, 8>("mpn_sub_4k_inplace 8");
    _1x::benchmark<0, 8>("mpn_sub_n 8");
    _1x::benchmark<5, 8>("mpn_sub_4k 8");
    _1x::benchmark<0, 16>("mpn_sub_n 16");
    _1x::benchmark<5, 16>("mpn_sub_4k 16");
    _1x::benchmark<0, 16>("mpn_sub_n 17");
    _1x::benchmark<6, 16>("/3 16");
    _1x::benchmark<6, 17>("/3 17");
    _1x::benchmark<7, 16>("<< 16");
    _1x::benchmark<7, 17>("<< 17");
}
