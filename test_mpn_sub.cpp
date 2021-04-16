// test of macro mpn_sub_4k() and mpn_sub8()

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "automagic/mpn_sub_4k.h"
#include "automagic/mpn_sub_8.h"
#include "automagic/mpn_sub_1x.h"

#define INT mp_limb_t
#define RAND_SEED 20190625

#include "test-internal.h"

INT g_src[48 * 2];                    // a, b taken from here
INT g_tgt_good[48];                   // r = a-b
INT g_tgt_baad[48];                   //         gets here

#define NS(x)                                                            \
    namespace _ ## x {                                                   \
    static constexpr uint16_t SIZE = x;                                  \
                                                                         \
    void                                                                 \
    call_good() {                                                        \
        (void)mpn_sub_n(g_tgt_good + 0, g_src + 0, g_src + SIZE, SIZE);  \
    }                                                                    \
                                                                         \
    void                                                                 \
    call_baad() {                                                        \
        auto r_p = g_tgt_baad + 0;                                       \
        auto a_p = g_src + 0;                                            \
        auto b_p = g_src + SIZE;                                         \
        uint16_t loop_count = (SIZE / 4) - 1;                            \
        mpn_sub_4k(r_p, a_p, b_p, loop_count);                           \
    }

NS(8)
// can't include line with # in macro definition, so add 2 lines
#include "test-mpn_sub-internal.h"
}

NS(16)
#include "test-mpn_sub-internal.h"
}

NS(48)
#include "test-mpn_sub-internal.h"
}

// test mpn_sub8()
namespace _8f {

static constexpr uint16_t SIZE = 8;

void
call_good() {
    (void)mpn_sub_n(g_tgt_good + 0, g_src + 0, g_src + SIZE, SIZE);
}

void
call_baad() {
    auto r_p = g_tgt_baad + 0;
    auto u_p = g_src + 0;
    auto v_p = g_src + SIZE;
    mpn_sub8(r_p, u_p, v_p);
}

#include "test-mpn_sub-internal.h"

} // end namespace _8f

#define NS_1(x)                                                          \
    namespace _ ## x {                                                   \
    static constexpr uint16_t SIZE = x;                                  \
                                                                         \
    void                                                                 \
    call_good() {                                                        \
        (void)mpn_sub_n(g_tgt_good + 0, g_src + 0, g_src + SIZE, SIZE);  \
    }                                                                    \
                                                                         \
    void                                                                 \
    call_baad() {                                                        \
        auto r_p = g_tgt_baad + 0;                                       \
        auto a_p = g_src + 0;                                            \
        auto b_p = g_src + SIZE;                                         \
        uint64_t n = SIZE;                                               \
        mpn_sub_1x(r_p, a_p, b_p, n);                                    \
    }

NS_1(5)
#include "test-mpn_sub-internal.h"
}

NS_1(6)
#include "test-mpn_sub-internal.h"
}

NS_1(9)
#include "test-mpn_sub-internal.h"
}


int
main() {
    _8::test();
    _8f::test();
    _16::test();
    _48::test();

    _5::test();
    _6::test();
    _9::test();

    printf("Test passed\n");
    return 0;
}
