static constexpr auto RESULT_SIZE = SIZE * 2 * sizeof(INT);
static constexpr auto OPERAND_SIZE = SIZE * sizeof(INT);

void
do_test() {
    call_good();
    call_baad();
    if (memcmp(g_result_good + 0, g_result_baad + 0, RESULT_SIZE)) {
        printf("Problem\n");
        dump_number(g_a, SIZE);
        dump_number(g_b, SIZE);
        dump_number(g_result_good + 0, SIZE * 2);
        dump_number(g_result_baad + 0, SIZE * 2);
        exit(1);
    }
}

void
junior_words(INT* t, unsigned x) {
    // x junior words := -1
    memset(t, 0, sizeof(INT) * SIZE);
    for(unsigned i = 0; i < x; i++) {
        t[i] = (INT)-1;
    }
}

void
test() {
    memset(g_a, 0, OPERAND_SIZE);
    memset(g_b, 0, OPERAND_SIZE);
    call_good();
    call_baad();
    if (memcmp(g_result_good + 0, g_result_baad + 0, RESULT_SIZE)) {
        printf("Problem with zero\n");
        dump_number(g_result_good + 0, SIZE * 2);
        dump_number(g_result_baad + 0, SIZE * 2);
        exit(1);
    }

    for(unsigned a = 0; a < BITS_PER_LIMB; a++) {
        deg2(g_a + 0, SIZE, a);
        for(unsigned b = 0; b < BITS_PER_LIMB; b++) {
            deg2(g_b + 0, SIZE, b);
            call_good();
            call_baad();
            if (memcmp(g_result_good + 0, g_result_baad + 0, RESULT_SIZE)) {
                printf("Problem for a=%u b=%d\n", a, b);
                dump_number(g_result_good + 0, SIZE * 2);
                dump_number(g_result_baad + 0, SIZE * 2);
                exit(1);
            }
        }
    }

    for(unsigned a = 0; a < SIZE; a++) {
        one_word(g_a + 0, SIZE, a);
        for(unsigned b = 0; b < SIZE; b++) {
            one_word(g_b + 0, SIZE, b);
            do_test();
        }
    }
    
    for(unsigned i = 0; i < SIZE; i++) {
        g_a[i] = ((INT)0x3) << 62;
    }
    memset(g_b, 0, sizeof(g_b));
    g_b[1] = g_b[0] = g_a[0];
    do_test();

    for(unsigned a = 0; a <= SIZE; a++) {
        junior_words(g_a + 0, a);
        for(unsigned b = 0; b <= SIZE; b++) {
            junior_words(g_b + 0, b);
            do_test();
        }
    }

    srand(RAND_SEED);
    for(unsigned i = 100; i--;) {
        random_number<INT>(g_a + 0, SIZE);
        random_number<INT>(g_b + 0, SIZE);
        do_test();
    }
}
