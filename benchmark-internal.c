#include <cstring>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <x86intrin.h>
#include <unistd.h>

#include "random-number.h"

uint64_t g_a[SIZE];

int
main(int c, char** v) {
    srand(atol(v[1]));
    auto page_size = sysconf(_SC_PAGE_SIZE);
    auto pool_0 = (uint64_t*)memalign(page_size, page_size);
    auto pool_1 = (uint64_t*)memalign(page_size, page_size);

    random_number<uint64_t>(g_a + 0, SIZE);
    random_number<uint64_t>(pool_0, SIZE);
    random_number<uint64_t>(pool_1, SIZE);

    auto mask = (page_size / sizeof(uint64_t) / 2) - 1;

    HELLO
    unsigned i = 0, j = SIZE;
    auto t = __rdtsc();
    for(long k = 0; k < VOLUME / 2; k++) {
        SUBR(pool_0 + j, pool_1 + i, g_a + 0);
        SUBR(pool_1 + j,  g_a + 0, pool_0 + i);
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
