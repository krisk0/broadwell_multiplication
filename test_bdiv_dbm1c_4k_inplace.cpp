// test of macro bdiv_dbm1c_4k_macro()

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "automagic/bdiv_dbm1c_4k_inplace.h"
#include "test-internal.h"

extern "C" {
INT __gmpn_bdiv_dbm1c(mp_ptr, mp_srcptr, mp_size_t, INT, INT);
}

#define RAND_SEED 20190731
#define MAX_SIZE 60

INT g_src[MAX_SIZE];                        // u taken from here
INT g_tgt_good[MAX_SIZE];                   // r = u/3 gets here
INT g_tgt_baad[MAX_SIZE];

template <uint16_t N>
void
do_test() {
    memcpy(g_tgt_good + 0, g_src + 0, sizeof(INT) * N);
    memcpy(g_tgt_baad + 0, g_src + 0, sizeof(INT) * N);

    (void)__gmpn_bdiv_dbm1c(g_tgt_good + 0, g_tgt_good + 0, N, GMP_NUMB_MASK / 3, 0);
    mpn_bdiv_dbm1c_4k_inplace_wr(g_tgt_baad + 0, N, GMP_NUMB_MASK / 3);

    if (!memcmp(g_tgt_good + 0, g_tgt_baad + 0, N * sizeof(INT))) {
        return;
    }

    printf("Problem\n");
    dump_number(g_src + 0, N);
    dump_number(g_tgt_good + 0, N);
    dump_number(g_tgt_baad + 0, N);
    exit(1);
}

template <uint16_t N>
void
test() {
    memset(g_src, 0, N * sizeof(INT));

    do_test<N>();

    for (int k = 100; k--;) {
        random_number<INT>(g_src + 0, N);
        do_test<N>();
    }
}

int
main() {
    test<4>();
    test<8>();
    test<12>();
    test<60>();
    printf("Test passed\n");
    return 0;
}
