// test macro mpn_mul2_add_4k()

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "automagic/mpn_mul2_add_4k.h"
#include "test-internal.h"

extern "C" {
mp_limb_t __gmpn_addlsh1_n(mp_ptr, mp_srcptr, mp_srcptr, mp_size_t);
}

#define MAX_SIZE 64
INT g_u[MAX_SIZE];
INT g_v[MAX_SIZE];
INT g_tgt_good[1 + MAX_SIZE];
INT g_tgt_baad[3 + MAX_SIZE]; // canary on the left, to detect
                              //  overruns in mpn_mul2_add_4k()

template <uint16_t N>
void
do_test(const char* m = NULL) {
    g_tgt_good[N] = __gmpn_addlsh1_n(g_tgt_good + 0, g_v + 0, g_u + 0, N);

    memset(g_tgt_baad + 0, 0x0F, (3 + N) * sizeof(INT));
    mpn_mul2_add_4k_wr(g_tgt_baad + 0, g_u + 0, g_v + 0, N/4);
    bool err = false;
    if(g_tgt_baad[1 + N] != 0x0F0F0F0F0F0F0F0F) {
        err = true;
        printf("Spoilt tgt[1+N]: " PRINTF_FORMAT "\n", g_tgt_baad[1 + N]);
    }
    if(g_tgt_baad[2 + N] != 0x0F0F0F0F0F0F0F0F) {
        err = true;
        printf("Spoilt tgt[2+N]: " PRINTF_FORMAT "\n", g_tgt_baad[2 + N]);
    }

    if(err || memcmp(g_tgt_good + 0, g_tgt_baad + 0, (1 + N) * sizeof(INT))) {
        if(m) {
            printf("Problem with %s\n", m);
        } else {
            printf("Problem with u, v\n");
            dump_number(g_u + 0, N);
            dump_number(g_v + 0, N);
        }
        dump_number(g_tgt_good + 0, 1 + N);
        dump_number(g_tgt_baad + 0, 1 + N);
        exit(1);
    }
}

template <uint16_t N>
void
test() {
    printf("Testing N=%u\n", N);
    memset(g_u + 0, 0, N * sizeof(INT));
    memset(g_v + 0, 0, N * sizeof(INT));
    do_test<N>("zero u and v");

    for(INT a = 0; a < N * 64; a++) {
        deg2(g_u + 0, N, a);
        for(INT b = 0; b < N * 64; b++) {
            deg2(g_v + 0, N, b);
            do_test<N>();
        }
    }

    for (int k = 100; k--;) {
        random_number<INT>(g_u + 0, N);
        random_number<INT>(g_v + 0, N);
        do_test<N>();
    }
}

template <uint16_t START, uint16_t END, uint16_t STEP>
void
many_tests() {
    test<START>();
    auto constexpr N = STEP + START;
    if constexpr (N <= END) {
        many_tests<N, END, STEP>();
    }
}

int
main() {
    many_tests<4, MAX_SIZE, 4>();

    printf("Test passed\n");
    return 0;
}
