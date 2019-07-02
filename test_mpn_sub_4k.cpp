// test of macro mpn_add_4k_inplace()

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "automagic/mpn_sub_4k_inplace.h"

#define INT mp_limb_t
#define RAND_SEED 20190626

#include "test-internal.h"


INT g_src[48 * 2];                    // a, b taken from here
INT g_tgt_good[48];                   // r = a+b gets here
INT g_a_saved[48];


#define NS(x)                                                            \
    namespace _ ## x {                                                   \
    static constexpr uint16_t SIZE = x;                                  \
                                                                         \
    mp_limb_t                                                            \
    call_good() {                                                        \
        memcpy(g_a_saved, g_src, SIZE * sizeof(INT));                    \
        return mpn_sub_n(g_tgt_good + 0, g_src + SIZE, g_src + 0, SIZE); \
    }                                                                    \
                                                                         \
    mp_limb_t                                                            \
    call_baad() {                                                        \
        auto a_p = g_src + 0;                                            \
        auto b_p = g_src + SIZE;                                         \
        uint16_t loop_count = (SIZE / 4) - 1;                            \
        mp_limb_t carry = 0;                                             \
        mpn_sub_4k_inplace(carry, a_p, b_p, loop_count);                 \
        return carry;                                                    \
    }


NS(8)
// can't include line with # in macro definition, so add 2 lines
#include "test-mpn_add_4k-internal.h"
}

NS(16)
#include "test-mpn_add_4k-internal.h"
}

NS(48)
#include "test-mpn_add_4k-internal.h"
}

int
main() {
    _8::test();
    _16::test();
    _48::test();

    printf("Test passed\n");
    return 0;
}
