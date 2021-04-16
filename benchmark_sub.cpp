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
#include "shift_avx2.h"

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

constexpr INT G_VOLUME = 1000*1000*800;

namespace _1x {

template <uint16_t WHAT, uint16_t SIZE>
void
subtr(mp_ptr u, mp_ptr v) {
    auto t = u + SIZE;
    INT size = SIZE;
    if constexpr (WHAT == 0) {
        mpn_sub_n(t, u, v, size);
    }
    if constexpr (WHAT == 1) {
        uint16_t s = size;
        mpn_sub_1x(t, u, v, s);
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
    if constexpr (WHAT == 8) {
        (void)mpn_rshift(u, v, SIZE, 1);
    }
    if constexpr (WHAT == 10) {
        (void)mpn_rshift(u, u, SIZE, 1);
    }
    if constexpr (WHAT == 9) {
        if constexpr (SIZE == 7) {
            shr1_7_avx2(u, v);
        }
        if constexpr (SIZE == 10) {
            shr1_10_avx2(u, v);
        }
        if constexpr (SIZE > 10) {
            auto constexpr k = (SIZE - 1) / 9;
            if constexpr (k * 9 == SIZE - 1) {
                auto kk = k;
                shr1_9k_plus1_avx2(u, kk);
            } else {
                auto constexpr k_again = (SIZE - 1) / 6;
                if constexpr (k_again * 6 == SIZE - 1) {
                    auto kk = k_again;
                    shr1_6k_plus1_avx2(u, kk);
                }
            }
        }
    }
}

template <uint16_t WHAT, uint16_t SIZE, INT VOLUME = G_VOLUME>
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

    #if 1
    _1x::benchmark<0, 7>("mpn_sub_n 7");
    _1x::benchmark<1, 7>("mpn_sub_1x 7");              // a lot slower, don't use
    _1x::benchmark<2, 7>("mpn_sub_n inplace 7");
    _1x::benchmark<3, 7>("mpn_sub_inplace 7");         // slightly slower, don't use
    _1x::benchmark<3, 17>("mpn_sub_inplace 17");
    _1x::benchmark<2, 17>("mpn_sub_n inplace 17");     //                            this
    _1x::benchmark<2, 8>("mpn_sub_n inplace 8");
    _1x::benchmark<4, 8>("mpn_sub_4k_inplace 8");
    _1x::benchmark<0, 8>("mpn_sub_n 8");
    _1x::benchmark<5, 8>("mpn_sub_4k 8");
    _1x::benchmark<0, 16>("mpn_sub_n 16");
    _1x::benchmark<5, 16>("mpn_sub_4k 16");
    _1x::benchmark<0, 16>("mpn_sub_n 17");
    _1x::benchmark<0, 31, G_VOLUME/2>("mpn_sub_n 31");
    _1x::benchmark<0, 32, G_VOLUME/2>("mpn_sub_n 32");
    _1x::benchmark<5, 32, G_VOLUME/2>("mpn_sub_4k 32");
    _1x::benchmark<4, 32, G_VOLUME/2>("mpn_sub_4k_inplace 32");
    _1x::benchmark<0, 63, G_VOLUME/4>("mpn_sub_n 63");
    _1x::benchmark<0, 64, G_VOLUME/4>("mpn_sub_n 64");
    _1x::benchmark<5, 64, G_VOLUME/4>("mpn_sub_4k 64");
    _1x::benchmark<4, 64, G_VOLUME/4>("mpn_sub_4k_inplace 64");
    _1x::benchmark<6, 16>("/3 16");
    _1x::benchmark<6, 17>("/3 17");
    _1x::benchmark<6, 61, G_VOLUME/8>("/3 61");
    _1x::benchmark<7, 16>("<<1 16");
    _1x::benchmark<7, 17>("<<1 17");     // 1.6 ticks per limb
    _1x::benchmark<7, 61, G_VOLUME/4>("<<1 61");     // 1.3 ticks per limb
    _1x::benchmark<8,  7>(">>1  7");
    _1x::benchmark<9,  7>(">|1  7");     // avx2 subroutine that shifts right
    _1x::benchmark<8, 10>(">>1 10");
    _1x::benchmark<9, 10>(">|1 10");     // avx2 subroutine that shifts right
    #endif
    _1x::benchmark<10, 19>(">>  19");     // mpn_rshift in-place
    _1x::benchmark< 9, 19>("|>1 19");     // avx2 in-place
    _1x::benchmark<10, 37>(">>  37");     // mpn_rshift in-place
    _1x::benchmark< 9, 37>("|>1 37");     // avx2 in-place
    _1x::benchmark<10, 61>(">>  61");     // mpn_rshift in-place
    _1x::benchmark< 9, 61>("|>1 61");     // avx2 in-place
    _1x::benchmark<10, 64>(">>  64");     // mpn_rshift in-place
    _1x::benchmark< 9, 64>("|>1 64");     // avx2 in-place
    #if 0
    _1x::benchmark<8, 16>(">>1 16");
    _1x::benchmark<8, 17>(">>1 17");     // same as left shift
    _1x::benchmark<8, 23>(">>1 23");
    _1x::benchmark<8, 24>(">>1 24");
    _1x::benchmark<8, 61, G_VOLUME/4>(">>1 61");
    #endif
}
