// test of macro mpn_sub_inplace()

#include <stdlib.h>
#include <cstdint>

#include <gmp.h>

#include "automagic/mpn_sub_inplace.h"

#define INT mp_limb_t
#define RAND_SEED 20190719

#include "test-internal.h"

#define MAX_SIZE 33

INT g_src[MAX_SIZE * 2];                    // a, b taken from here
INT g_tgt_good[MAX_SIZE];                   // r = a-b gets here
INT g_a_saved[MAX_SIZE];


#define NS(x)                                                            \
    namespace _ ## x {                                                   \
    constexpr uint16_t SIZE = x;                                         \
                                                                         \
    INT                                                                  \
    call_good() {                                                        \
        memcpy(g_a_saved, g_src, SIZE * sizeof(INT));                    \
        return mpn_sub_n(g_tgt_good + 0, g_src + SIZE, g_src + 0, SIZE); \
    }                                                                    \
                                                                         \
    INT                                                                  \
    call_baad() {                                                        \
        auto a_p = g_src + 0;                                            \
        auto b_p = g_src + SIZE;                                         \
        INT n = SIZE;                                                    \
        mpn_sub_inplace(a_p, b_p, n);                                    \
        return n;                                                        \
    }


NS(5)
// can't include line with # in macro definition, so add 2 lines
#include "test-mpn_add_4k-internal.h"
}

NS(10)
#include "test-mpn_add_4k-internal.h"
}

NS(23)
#include "test-mpn_add_4k-internal.h"
}

NS(33)
#include "test-mpn_add_4k-internal.h"
}


int
main() {
    _5::test();
    _10::test();
    _23::test();
    _33::test();

    printf("Test passed\n");
    return 0;
}
