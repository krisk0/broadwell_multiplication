// benchmark multiplication subrouitine CALL(rp, ap, bp, n), adjusting volume dynamically

#include <time.h>

#include "random-number.h"

namespace benchmark_dynamic {

INT* g_pool_0;
INT* g_pool_1;
INT* g_a;

template <uint16_t NOW, uint16_t LIMIT>
void
do_test(INT volume) {
    random_number<INT>(g_a, NOW);
    random_number<INT>(g_pool_0, NOW);
    random_number<INT>(g_pool_1, NOW);

    auto mask = (g_page_size / sizeof(INT) / 2) - 1;
    INT i = 0, j = NOW;
    printf("Testing size %u, volume=%ld\n", NOW, volume);
    auto seconds = time(NULL);
    auto ticks = __rdtsc();
    for(INT k = volume / 2; k--;) {
        CALL(g_pool_0 + j, g_pool_1 + i, g_a, NOW);
        CALL(g_pool_1 + j, g_a, g_pool_0 + i, NOW);
        i = (i + 1) & mask;
        j = (j + NOW * 2) & mask;
    }
    ticks = __rdtsc() - ticks;
    seconds = time(NULL) - seconds;

    auto cycles = ticks / volume;
    printf("size=%u  spent %ld sec/%lld ticks  ticks per multiplication %lld\n", NOW,
            seconds, ticks, cycles);
    
    if (seconds) {
        // adjust volume so next experiment with same 'NOW' value takes 4 seconds
        volume = INT(double(2) * volume / seconds) * 2;
    } else {
        // too fast, increase volume 10 times
        volume *= 10;
    }
    
    if constexpr (NOW < LIMIT) {
        do_test<1 + NOW, LIMIT>(volume);
    }
}

template <uint16_t ALPHA, uint16_t BETTA>
void
test(INT volume) {
    bordeless_alloc_nodefine(INT, g_pool_0, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc_nodefine(INT, g_pool_1, g_page_size, g_page_mask, g_page_unmask);
    bordeless_alloc_nodefine(INT, g_a, BETTA * sizeof(INT), g_page_mask, g_page_unmask);
    
    do_test<ALPHA, BETTA>(volume);
}

} // end namespace benchmark_dynamic
