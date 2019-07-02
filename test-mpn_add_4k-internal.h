void
test_slave() {
    auto good_carry = call_good(); // result in g_tgt_good[], copy of operand saved
    auto baad_carry = call_baad(); // result in g_src[]
    auto carry_mismatch = good_carry != baad_carry;
    auto major_mismatch = !!memcmp(g_tgt_good, g_src, SIZE * sizeof(INT));
    if (carry_mismatch || major_mismatch) {
        printf("Problem\n");
        dump_number(g_a_saved + 0, SIZE);    // using copy created inside call_good()
        dump_number(g_src + SIZE, SIZE);
        if (carry_mismatch) {
            printf("carry mismatches\n");
            printf("carry good/baad: %ld/%ld\n", good_carry, baad_carry);
        }
        if (major_mismatch) {
            printf("main result mismatches\n");
            dump_number(g_tgt_good + 0, SIZE);
            dump_number(g_src + 0, SIZE);
        }
        exit(1);
    }
}

void
test() {
    memset(g_src, 0, sizeof(g_src));
    memset(g_tgt_good, 0, sizeof(g_tgt_good));
    test_slave();

    for (int i = 0; i < SIZE; i++) {
        memset(g_src, 0, sizeof(g_src));
        g_src[SIZE + i] = 1;
        test_slave();
    }

    for (int i = 0; i < SIZE; i++) {
        memset(g_src, 0, sizeof(g_src));
        g_src[i] = 1;
        test_slave();
    }
    
    srand(RAND_SEED);
    for(unsigned i = 100; i--;) {
        random_number<INT>(g_src + 0, 2 * SIZE);
        test_slave();
    }
}
