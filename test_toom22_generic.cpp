// test subroutine toom22_deg2_broadwell() or toom22_deg2_broadwell_n<>()

#include <cstdint>

#include <gmp.h>

#include "test-internal.h"

#include "automagic/toom22_mul_16.h"
#include "automagic/toom22_generic_aux.h"
#include "toom22_generic.h"

#define MAX_N 128
#define RAND_SEED 20190626

INT* g_scratch;
INT g_a[MAX_N];
INT g_b[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];

#if TEMPLATE
    #define BAAD(a, b, c, d) toom22_deg2_broadwell_n<SIZE>(a, b, c, d)
#else
    #define BAAD(a, b, c, d) toom22_deg2_broadwell(a, b, c, d, SIZE)
#endif

#define NS(x)                                                                        \
    namespace _ ## x {                                                               \
    static constexpr uint16_t SIZE = x;                                              \
                                                                                     \
    void call_good() {                                                               \
        mpn_mul_n(g_result_good + 0, g_a + 0, g_b + 0, SIZE);                        \
    }                                                                                \
                                                                                     \
    void call_baad() {                                                               \
        BAAD(g_result_baad + 0, g_scratch, g_a + 0, g_b + 0);                        \
    }

NS(32)
#include "test-toom22_generic-internal.h"
}

NS(64)
#include "test-toom22_generic-internal.h"
}

NS(128)
#include "test-toom22_generic-internal.h"
}

int
main() {
    g_scratch = (INT*)malloc(sizeof(INT) * toom22_generic_itch(MAX_N));

    _32::test();
    _64::test();
    _128::test();

    printf("Test passed\n");
    return 0;
}
