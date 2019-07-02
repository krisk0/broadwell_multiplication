#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "test-internal.h"
#include "automagic/mpn_less_3arg.h"
#include "automagic/mpn_le_8.h"

#define RAND_SEED 20190625

mp_limb_t g_playground[2 * 8];

uint16_t
call_3arg() {
    uint16_t result;
    auto a_tail = g_playground + 8;
    auto b_tail = a_tail + 8;
    mpn_less_3arg(result, a_tail, b_tail);
    return result;
}

mp_limb_t
call_mpn_le_8() {
    mp_limb_t result;
    auto a_p = g_playground + 0;
    auto b_p = g_playground + 8;
    mpn_le_8(result, a_p, b_p);
    return result;
}

void
test_slave() {
    auto good = call_mpn_le_8();
    auto baad = call_3arg();
    if (good != baad) {
        dump_number(g_playground, 8);
        dump_number(g_playground + 8, 8);
        printf("good=%ld baad=%ld\n", good, (uint64_t)baad);
        exit(1);
    }
}

int
main() {
    memset(g_playground, 0, sizeof(g_playground));
    test_slave();
    
    srand(RAND_SEED);
    for(unsigned i = 100; i--;) {
        random_number<INT>(g_playground + 0, 16);
        test_slave();
    }
    
    printf("Test passed\n");
    return 0;
}
