/*
test subroutines
 * toom22_deg2_broadwell()
 * toom22_deg2_broadwell_t<>()
 * toom22_12_broadwell()
 * toom22_12e_broadwell()
 * toom22_12_broadwell_n<>()
*/

#include "toom22_generic.h"

#include "test-internal.h"

#define MAX_N 128
#define RAND_SEED 20190626

INT* g_scratch;
INT g_a[MAX_N];
INT g_b[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];

#if TEMPLATE
    #define BAAD(a, b, c, d) toom22_deg2_broadwell_t<SIZE>(a, b, c, d)
#else
    #define BAAD(a, b, c, d) toom22_deg2_broadwell(a, b, c, d, SIZE)
#endif

#define NS(x)                                                                        \
    namespace _ ## x {                                                               \
    constexpr uint16_t SIZE = x;                                                     \
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

template <uint16_t N>
void
toom22_12(mp_ptr a, mp_ptr b, mp_srcptr c, mp_srcptr d) {
    #if TEMPLATE
        toom22_12_broadwell_t<N>(a, b, c, d);
    #else
        if constexpr (N == 12) {
            toom22_12e_broadwell(a, b, c, d);
        } else {
            toom22_12_broadwell(a, b, c, d, N);
        }
    #endif
}

#define NS_12(x)                                                                     \
    namespace _ ## x {                                                               \
    constexpr uint16_t SIZE = x;                                                     \
                                                                                     \
    void call_good() {                                                               \
        mpn_mul_n(g_result_good + 0, g_a + 0, g_b + 0, SIZE);                        \
    }                                                                                \
                                                                                     \
    void call_baad() {                                                               \
        toom22_12<SIZE>(g_result_baad + 0, g_scratch, g_a + 0, g_b + 0);             \
    }

NS_12(12)
#include "test-toom22_generic-internal.h"
}
NS_12(24)
#include "test-toom22_generic-internal.h"
}
NS_12(48)
#include "test-toom22_generic-internal.h"
}
NS_12(96)
#include "test-toom22_generic-internal.h"
}

int
main() {
    g_scratch = (INT*)malloc(sizeof(INT) * toom22_itch_broadwell_t<MAX_N>());
    _32::test();
    _64::test();
    _128::test();
    free(g_scratch);

    g_scratch = (INT*)malloc(sizeof(INT) * toom22_itch_broadwell_t<MAX_N>());
    _12::test();
    _24::test();
    _48::test();
    _96::test();
    free(g_scratch);

    printf("Test passed\n");
    return 0;
}
