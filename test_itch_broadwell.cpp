// Test itch::toom22_t against toom22_itch_broadwell

#include <toom22_generic.h>

/*
g++ version 9.3.0 has problem unrolling do_test<i, b> for i in 1..128: code does not
 compile in reasonable time. Therefore unrolling code via python
*/

bool g_failed = false;

template<uint16_t N, uint16_t B>
void
do_test() {
    auto good = toom22_itch_broadwell(N, B);
    auto baad = itch::toom22_t<N, B>();
    if (good != baad) {
        printf("Problem for N=%d, B=%d: %lu/%lu\n", N, B, good, baad);
        g_failed = true;
    }
}

int
main() {
    // code unrolled via python
    #include "automagic/test_itch_broadwell.h"
    if (!g_failed) {
        printf("Test passed\n");
    }
    return 0;
}
