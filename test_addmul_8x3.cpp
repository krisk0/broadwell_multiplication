#include "dump-number.h"
#include "toom22_generic.h"

#if defined(EXTRA_INCLUDE)
    #include EXTRA_INCLUDE
#endif

#ifndef TESTED
    #define TESTED addmul_8x3
#endif

#define GOOD(r, u, v) addmul_8x3_slow(r, u, v)
#define BAAD(r, u, v) TESTED(r, u, v)
#define RAND_SEED 20210114

void
test_3arg(mp_ptr c, mp_ptr u, mp_ptr v) {
    INT r0[14], r1[14];

    memcpy(r0 + 0, c + 0, sizeof(r0));
    GOOD(r0 + 0, u, v);

    memcpy(r1 + 0, c + 0, sizeof(r0));
    BAAD(r1 + 0, u, v);

    if (memcmp(r0 + 0, r1 + 0, sizeof(r0))) {
        printf("Problem\n");
        dump_number(c + 0, 14);
        dump_number(u, 8);
        dump_number(v, 3);
        dump_number(r0 + 0, 14);
        dump_number(r1 + 0, 14);
        exit(1);
    }
}

void
single_one_in_u_v(mp_ptr c, mp_ptr u, mp_ptr v) {
    for(unsigned i = 0; i < 8 * BITS_PER_LIMB; i++) {
        deg2(u, 8, i);
        for(unsigned j = 0; j < 3 * BITS_PER_LIMB; j++) {
            deg2(v, 3, j);
            //printf("i,j=%u,%u\n", i, j);
            test_3arg(c, u, v);
        }
    }

    memset(u, 0, 8 * sizeof(INT));
    memset(v, 0, 3 * sizeof(INT));
}

void
do_test_addmul() {
    INT c[14], u[8], v[3];

    memset(c + 0, 0, sizeof(c));
    single_one_in_u_v(c + 0, u + 0, v + 0);

    memset(u + 0, 0, sizeof(u));
    memset(v + 0, 0, sizeof(v));
    for(unsigned d = 0; d < BITS_PER_LIMB * 14; d++) {
        deg2(c + 0, 14, d);
        test_3arg(c + 0, u + 0, v + 0);
        single_one_in_u_v(c + 0, u + 0, v + 0);
    }
}

int main() {
    do_test_addmul();

    printf("Test passed\n");
    return 0;
}
