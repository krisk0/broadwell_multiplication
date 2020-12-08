/*
test subroutine toom22_xx_broadwell(). As a side effect, the following procedures
 are tested:
 * toom22_deg2_broadwell()
 * toom22_12_broadwell()
 * toom22_12e_broadwell()
 * toom22_1x_broadwell()
 * toom22_2x_broadwell()
 * toom22_8x_broadwell()
*/

#define LOUD 0

#include "toom22_generic.h"

#include "test-internal.h"

#define MAX_N 128
#define RAND_SEED 20190719

INT* g_scratch;
INT g_a[MAX_N];
INT g_b[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];
INT g_size;

char g_print_scratch[1000];

INT g_result_size = g_size * 2 * sizeof(INT);
INT g_operand_size = g_size * sizeof(INT);

void
junior_words(INT* t, unsigned x) {
    // x junior words := -1
    memset(t, 0, g_operand_size);
    for(unsigned i = 0; i < x; i++) {
        t[i] = (INT)-1;
    }
}

void
call_good() {
    mpn_mul_n(g_result_good + 0, g_a + 0, g_b + 0, g_size);
}

void
call_baad() {
    toom22_xx_broadwell(g_result_baad + 0, g_scratch, g_a + 0, g_b + 0, (uint16_t)g_size);
}

void
test_slave(const char* m) {
    call_good();
    call_baad();
    if (!memcmp(g_result_good, g_result_baad, g_operand_size)) {
        return;
    }
    printf("%s, size=%lu\n", m, g_size);
    dump_number(g_a, g_size);
    dump_number(g_b, g_size);
    dump_number(g_result_good + 0, g_size * 2);
    dump_number(g_result_baad + 0, g_size * 2);
    exit(1);
}

void
do_test() {
    g_result_size = g_size * 2 * sizeof(INT);
    g_operand_size = g_size * sizeof(INT);

    memset(g_a, 0, g_operand_size);
    memset(g_b, 0, g_operand_size);
    test_slave("Problem with zero");

    for(unsigned a = 0; a < BITS_PER_LIMB; a++) {
        deg2(g_a + 0, g_size, a);
        for(unsigned b = 0; b < BITS_PER_LIMB; b++) {
            deg2(g_b + 0, g_size, b);
            sprintf(g_print_scratch, "Problem for a=%u b=%u\n", a, b);
            test_slave(g_print_scratch);
        }
    }

    for(unsigned a = 0; a < g_size; a++) {
        one_word(g_a + 0, g_size, a);
        for(unsigned b = 0; b < g_size; b++) {
            one_word(g_b + 0, g_size, b);
            test_slave("Problem with one word");
        }
    }
    
    for(unsigned i = 0; i < g_size; i++) {
        g_a[i] = ((INT)0x3) << 62;
    }
    memset(g_b, 0, g_operand_size);
    g_b[1] = g_b[0] = g_a[0];
    test_slave("Problem with 3");

    for(unsigned a = 0; a <= g_size; a++) {
        junior_words(g_a + 0, a);
        for(unsigned b = 0; b <= g_size; b++) {
            junior_words(g_b + 0, b);
            test_slave("Problem with junior words");
        }
    }

    for(unsigned i = 100; i--;) {
        random_number<INT>(g_a + 0, g_size);
        random_number<INT>(g_b + 0, g_size);
        test_slave("Problem with random operands");
    }
}

int
main() {
    srand(RAND_SEED);
    g_scratch = (INT*)malloc(sizeof(INT) * toom22_itch_broadwell_t<MAX_N>());

    for (g_size = TOOM_2X_BOUND; g_size <= MAX_N; g_size++) {
        #if LOUD
            printf("size=%lu\n", g_size);
        #endif
        do_test();
    }

    free(g_scratch);
    
    printf("Test passed\n");
    return 0;
}
