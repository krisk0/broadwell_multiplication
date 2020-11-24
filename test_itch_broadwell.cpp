// Test toom22_itch_broadwell_t against toom22_itch_broadwell

#include <toom22_generic.h>

/*
g++ version 9.3.0 has problem unrolling do_test<1,128>: code does not compile
 in reasonable time. Therefore unrolling code via python

bool
do_test() {
    auto g = toom22_itch_broadwell(alpha);
    auto b = toom22_itch_broadwell_t<alpha>();
    if (g != b) {
        printf("Problem for i=%d\n: %lud/%lud\n", alpha, g, b);
        return false;
    }
    if (alpha < betta) {
        return do_test<alpha + 1, betta>();
    }
    return true;
}
*/

bool g_failed = false;

template<uint16_t N>
void
do_test() {
    auto g = toom22_itch_broadwell(N);
    auto b = toom22_itch_broadwell_t<N>();
    if (g != b) {
        printf("Problem for i=%d: %lu/%lu\n", N, g, b);
        g_failed = true;
    }
}

int
main() {
    // Due to bug in g++ code unrolled via python
    #include "automagic/test_itch_broadwell.h"
    if (!g_failed) {
        printf("Test passed\n");
    }
    return 0;
}
