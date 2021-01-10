#include <unistd.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "random-number.h"

#ifndef PRINTF_FORMAT
    #define PRINTF_FORMAT "%016lX"
#endif

#ifndef INT
    #define INT uint64_t
#endif

void
dump_number(const INT* p, unsigned n) {
    for(unsigned i = n; i--;) {
        printf("%X:" PRINTF_FORMAT " ", i, p[i]);
    }
    printf("\n");
}

#define BITS_PER_LIMB (sizeof(INT) * 8)

void
deg2(INT* t, unsigned size, unsigned x) {
    // set one bit
    auto i = x / BITS_PER_LIMB;
    x -= i * BITS_PER_LIMB;
    memset(t, 0, sizeof(INT) * size);
    t[i] = (INT(1)) << x;
}

void
one_word(INT* t, unsigned size, unsigned x) {
    // one word -1
    memset(t, 0, sizeof(INT) * size);
    t[x] = (INT)-1;
}

#ifdef GOOD

INT g_u[SIZE];
#ifndef V_ALREADY_DEFINED
    INT g_v[SIZE];
#endif
INT g_good[SIZE * 2];
INT g_baad[SIZE * 2];

void
junior_words(INT* t, unsigned x) {
    // x junior words := -1
    memset(t, 0, sizeof(INT) * SIZE);
    for(unsigned i = 0; i < x; i++) {
        t[i] = (INT)-1;
    }
}

void
test_uv(INT* u, INT* v) {
    GOOD(g_good + 0, u, v);
    BAAD(g_baad + 0, u, v);
    if (memcmp(g_good + 0, g_baad + 0, SIZE * 2 * sizeof(INT))) {
        printf("Problem\n");
        dump_number(u, SIZE);
        dump_number(v, SIZE);
        dump_number(g_good + 0, SIZE * 2);
        dump_number(g_baad + 0, SIZE * 2);
        exit(1);
    }
}

uint64_t
single_byte(uint64_t x) {
    uint8_t a[8];
    a[0] = x;
    for(int i = 1; i < 8; i++) {
        a[i] = 1 + a[i - 1];
    }
    memcpy(&x, a+0, sizeof(x));
    return x;
}

void
do_test() {
    for(unsigned a = 0; a < BITS_PER_LIMB * SIZE; a++) {
        deg2(g_u + 0, SIZE, a);
        for(unsigned b = 0; b < BITS_PER_LIMB * SIZE; b++) {
            deg2(g_v + 0, SIZE, b);
            for(unsigned x = 0; x < SIZE * 2; x++) {
                g_baad[x] = single_byte(x + 1);
            }
            GOOD(g_good + 0, g_u + 0, g_v + 0);
            BAAD(g_baad + 0, g_u + 0, g_v + 0);
            if (memcmp(g_good + 0, g_baad + 0, SIZE * 2 * sizeof(INT))) {
                fprintf(stderr, "Problem for a=%u b=%d\n", a, b);
                dump_number(g_good + 0, SIZE * 2);
                dump_number(g_baad + 0, SIZE * 2);
                exit(1);
            }
        }
    }

    for(unsigned a = 0; a < SIZE; a++) {
        one_word(g_u + 0, SIZE, a);
        for(unsigned b = 0; b < SIZE; b++) {
            one_word(g_v + 0, SIZE, b);
            test_uv(g_u + 0, g_v + 0);
            test_uv(g_v + 0, g_u + 0);
        }
    }
    
    for(unsigned i = 0; i < SIZE; i++) {
        g_u[i] = ((INT)0x3) << 62;
    }
    memset(g_v, 0, sizeof(g_v));
    g_v[1] = g_v[0] = g_u[0];
    test_uv(g_u + 0, g_v + 0);

    for(unsigned a = 0; a <= SIZE; a++) {
        junior_words(g_u + 0, a);
        for(unsigned b = 0; b <= SIZE; b++) {
			if(a > b) {
				continue;
			}
            junior_words(g_v + 0, b);
            test_uv(g_u + 0, g_v + 0);
            if(a < b) {
				test_uv(g_v + 0, g_u + 0);
			}
        }
    }

    srand(RAND_SEED);
    for(unsigned i = 100; i--;) {
        random_number<INT>(g_u + 0, SIZE);
        random_number<INT>(g_v + 0, SIZE);
        test_uv(g_u + 0, g_v + 0);
    }
}

#endif
