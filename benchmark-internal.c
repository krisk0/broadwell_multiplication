#include <stdlib.h>
#include <string.h>

#include "bordeless-alloc.h"
#include "random-number.h"

#define INT mp_limb_t

INT g_page_size;
INT g_page_mask;
INT g_page_unmask;

int
main(int, char** p) {
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    g_page_size = 1 + g_page_mask;
    srand(atol(p[1]));
    bordeless_alloc(INT, pool_0, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc(INT, pool_1, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc(INT, ap, SIZE * sizeof(INT), g_page_mask, g_page_unmask);

    random_number<INT>(ap, SIZE);
    random_number<INT>(pool_0, SIZE);
    random_number<INT>(pool_1, SIZE);

    auto mask = (g_page_size / sizeof(INT) / 2) - 1;

    HELLO
    unsigned i = 0, j = SIZE;
    auto t = __rdtsc();
    for(unsigned k = VOLUME / 2; k--;) {
        SUBR(pool_0 + j, pool_1 + i, ap);
        SUBR(pool_1 + j, ap, pool_0 + i);
        i = (i + 1) & mask;
        j = (j + SIZE * 2) & mask;
    }
    t = __rdtsc() - t;
    auto cycles = t / VOLUME;
    j = (j + mask - 1 - SIZE * 2) & mask;
    printf("spent %lld   ticks %lld   result %lX\n", t, cycles, pool_1[j]);
    GOODBYE

    return 0;
}
