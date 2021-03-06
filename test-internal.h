#include "dump-number.h"

#ifdef GOOD

#ifndef U_ALREADY_DEFINED
    INT g_u[SIZE];
#endif
#ifndef V_ALREADY_DEFINED
    INT g_v[SIZE];
#endif
INT g_good[SIZE * 2];
#ifndef R_ALREADY_DEFINED
    INT g_baad[SIZE * 2];
#endif

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
    memcpy(&x, a + 0, sizeof(x));
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
    memset(g_v + 0, 0, SIZE * sizeof(mp_limb_t));
    #if SIZE > 1
    g_v[1] =
    #endif
            g_v[0] = g_u[0];
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
