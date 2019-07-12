#include <cstdint>

#include <gmp.h>

#include "test-internal.h"

#include "automagic/toom22_mul_16.h"
#include "automagic/toom22_generic_aux.h"
#include "toom22_generic.h"

#define MAX_L 4

#define SIZE ((1 + MAX_L) * 4)

#define RAND_SEED 20190712

INT g_t0[SIZE];                 // result of slow::...
INT g_t1[SIZE];                 // result of fast::...
INT g_a[SIZE * 2];              // a then b
INT* g_b;                       // pointer to b
INT g_s[SIZE];                  // saved t

void
do_test(unsigned n, unsigned lc) {
    unsigned bytes = sizeof(INT) * n;
    memcpy(g_t1 + 0, g_t0 + 0, bytes);
    memcpy(g_s + 0, g_t0 + 0, bytes);

    auto c0 = mpn_add_2_4arg_slow(g_t0 + 0, g_a + 0, n, lc);
    auto c1 = mpn_add_2_4arg(g_t1 + 0, g_a + 0, n, lc);
    auto e1 = (bool)memcmp(g_t0 + 0, g_t1 + 0, bytes);
    auto err = (c0 != c1) || e1;

    if (not err) {
        return;
    }

    printf("Problem\n");
    dump_number(g_s + 0, n);
    dump_number(g_a + 0, n);
    dump_number(g_b + 0, n);
    if (c0 != c1) {
        printf("c0 = " PRINTF_FORMAT " != " PRINTF_FORMAT " = c1\n", c0, c1);
    }
    if (e1) {
        printf("r0:\n");
        dump_number(g_t0 + 0, n);
        printf("r1:\n");
        dump_number(g_t1 + 0, n);
    }
}

void
do_it(unsigned lc) {
    unsigned size = (1 + lc) * 4;
    g_b = g_a + size;
    for (int i = 0; i < SIZE; i++) {
        g_t0[i] = 1 + i;
        g_a[i] = 1;
        g_b[i] = 2;
    }
    do_test(size, lc);

    srand(RAND_SEED);
    for (int i = 100; i--; ) {
        random_number<INT>(g_a + 0, size);
        random_number<INT>(g_b + 0, size);
        random_number<INT>(g_t0 + 0, size);
        do_test(size, lc);
    }
}

int
main(int c, char** v) {
    do_it(1);
    do_it(MAX_L);

    printf("Test passed\n");
    return 0;
}
