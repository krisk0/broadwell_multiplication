#include <cstdint>
#include <cstring>
#include <cstdlib>

#include "random-number.h"
#include "test-internal.h"
#include "toom22_generic.h"

static constexpr uint16_t N = 14;
static constexpr uint16_t loops = N / 4;
static constexpr uint16_t M = N + 3;
static constexpr uint64_t RAND_SEED = 20210110;
static constexpr uint64_t VOLUME = 10000;

void
really_do_test(mp_ptr a, mp_ptr b) {
    if (b[M - 1] + 1 == 0) {
        b[M - 1]--;
    }
    mp_limb_t r0[M], r1[M];

    memcpy(r0 + 0, b + 0, sizeof(r0));
    mpn_add_n_plus_1(r0 + 0, a[N], a + 0, N);

    memcpy(r1 + 0, b + 0, sizeof(r0));
    mpn_add_4k_plus2_4arg(r1 + 0, a[N], a + 0, loops);

    if (memcmp(r0, r1, sizeof(r0))) {
        printf("Problem\n");
        dump_number(a + 0, N + 1);
        dump_number(b + 0, M);
        dump_number(r0, M);
        dump_number(r1, M);
        exit(1);
    }
}

void
do_test() {
    mp_limb_t a[N + 1], b[M];
    random_number<mp_limb_t>(a + 0, N + 1);
    random_number<mp_limb_t>(b + 0, M);

    really_do_test(a + 0, b + 0);
}

void
do_simple_test() {
    mp_limb_t a[N + 1], b[M];
    for(int i = 0; i < M; i++) {
        b[i] = 1 + i;
        if (i < N + 1) {
            a[i] = 1 + i;
        }
    }
    really_do_test(a + 0, b + 0);
}

int
main() {
    srand(RAND_SEED);

    do_simple_test();

    for(uint64_t i = 0; i < VOLUME; i++) {
        do_test();
    }

    printf("Test passed\n");
}
