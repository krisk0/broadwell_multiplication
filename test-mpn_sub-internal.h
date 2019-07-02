void
test_slave() {
    call_good();
    memset(g_tgt_baad, 0x34, sizeof(g_tgt_baad));
    call_baad();
    if (memcmp(g_tgt_good, g_tgt_baad, SIZE * sizeof(INT))) {
        printf("Problem\n");
        dump_number(g_src + 0, SIZE);
        dump_number(g_src + SIZE, SIZE);
        dump_number(g_tgt_good + 0, SIZE);
        dump_number(g_tgt_baad + 0, SIZE);
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
    
    srand(RAND_SEED);
    for(unsigned i = 100; i--;) {
        random_number<INT>(g_src + 0, 2 * SIZE);
        test_slave();
    }
}
