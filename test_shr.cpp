// test of macros that shift right

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "shift_avx2.h"
#include "test-internal.h"

#define MAX_SIZE 64
INT g_src[MAX_SIZE];                        // u taken from here
INT g_tgt_good[MAX_SIZE];                   // r = u/2 gets here
INT g_tgt_baad[MAX_SIZE];

template <uint16_t N, uint8_t SMART>
void
do_test() {
    (void)mpn_rshift(g_tgt_good + 0, g_src + 0, N, 1);
    if constexpr (N == 4) {
        shr1_4_avx2(g_tgt_baad + 0, g_src + 0);
    }
    if constexpr (N == 7) {
        shr1_7_avx2(g_tgt_baad + 0, g_src + 0);
    }
    if constexpr (N == 10) {
        if constexpr (SMART) {
            uint16_t k = 1;
            memcpy(g_tgt_baad + 0, g_src + 0, N * sizeof(INT));
            auto a = g_tgt_baad + 0;
            shr1_9k_plus1_avx2(a, k);
        } else {
            shr1_10_avx2(g_tgt_baad + 0, g_src + 0);
        }
    }
    if constexpr (N > 10) {
        auto constexpr k = (N - 1) / 9;
        memcpy(g_tgt_baad + 0, g_src + 0, N * sizeof(INT));
        auto a = g_tgt_baad + 0;
        if constexpr (k * 9 == N - 1) {
            auto kk = k;
            shr1_9k_plus1_avx2(a, kk);
        } else {
            auto constexpr k = (N - 1) / 6;
            static_assert(k * 6 == N - 1);
            auto kk = k;
            shr1_6k_plus1_avx2(a, kk);
        }
    }

    if (!memcmp(g_tgt_good + 0, g_tgt_baad + 0, N * sizeof(INT))) {
        return;
    }

    printf("Problem\n");
    dump_number(g_src + 0, N);
    dump_number(g_tgt_good + 0, N);
    dump_number(g_tgt_baad + 0, N);
    exit(1);
}

template <uint16_t N, uint8_t SMART=0>
void
test() {
    printf("Testing N=%u\n", N);
    memset(g_src, 0, N * sizeof(INT));
    do_test<N, SMART>();

    for(INT i = 0; i < N; i++) {
        g_src[i] = 1 + i;
    }
    do_test<N, SMART>();

    memset(g_src, 0xFF, N * sizeof(INT));
    do_test<N, SMART>();

    memset(g_src, 0xFE, N * sizeof(INT));
    do_test<N, SMART>();

    memset(g_src, 0x8F, N * sizeof(INT));
    do_test<N, SMART>();

    memset(g_src, 0x8E, N * sizeof(INT));
    do_test<N, SMART>();

    for (int k = 100; k--;) {
        random_number<INT>(g_src + 0, N);
        do_test<N, SMART>();
    }
}

template <uint16_t START, uint16_t END, uint16_t STEP>
void
many_tests() {
    test<START, 0>();
    auto constexpr N = STEP + START;
    if constexpr (N <= END) {
        many_tests<N, END, STEP>();
    }
}

int
main() {
    test<4>();
    test<7>();
    test<10>();
    test<10, 1>();
    
    many_tests<19, 64, 9>();
    many_tests<13, 49, 6>();

    printf("Test passed\n");
    return 0;
}
