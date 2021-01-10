#include <cstdint>
#include <cstring>
#include <cstdlib>

#include "random-number.h"
#include "test-internal.h"
#include "toom22_generic.h"

static constexpr uint16_t N = 14;
static constexpr uint16_t loops = N / 4;
static constexpr uint64_t RAND_SEED = 20210110;
static constexpr uint64_t VOLUME = 10000;

void
really_do_test(mp_ptr a, mp_ptr b) {
    mp_limb_t r0[N], a_copy[N], b_copy[N];

    auto c0 = mpn_sub_n(r0 + 0, a + 0, b + 0, N);
    
    memcpy(a_copy + 0, a, sizeof(a_copy));
    memcpy(b_copy + 0, b, sizeof(a_copy));
    auto c1 = mpn_sub_2k_plus2_inplace(b + 0, a + 0, loops);

    if (memcmp(a, a_copy, sizeof(a_copy))) {
        printf("2nd arg spoilt\n");
        exit(1);
    }
    
    if (memcmp(r0, b, sizeof(r0)) || (c0 != c1)) {
        printf("Problem with result\n");
        dump_number(a_copy + 0, N);
        dump_number(b_copy + 0, N);
        printf("c0 / 1 = %u / %u\n", (unsigned)c0, (unsigned)c1);
        dump_number(r0, N);
        dump_number(b, N);
        exit(1);
    }
}

void
do_test() {
    mp_limb_t a[N], b[N];
    random_number<mp_limb_t>(a + 0, N);
    random_number<mp_limb_t>(b + 0, N);

    really_do_test(a + 0, b + 0);
}

void
do_simple_test() {
    mp_limb_t a[N], b[N];
    for(int i = 0; i < N; i++) {
        b[i] = 1 + i;
        a[i] = 2 + i;
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
