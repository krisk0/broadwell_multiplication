/*
Make sure 3rd argument to SUBR is somehow aligned.

If ALIGN16=8, then the 3rd argument is at 16x+8. If ALIGN16=0, then the 3rd argument
 is at 16x.
*/

#include <stdlib.h>
#include <string.h>

#include "bordeless-alloc.h"
#include "random-number.h"

#define INT mp_limb_t

int
main(int, char** p) {
    INT page_size = sysconf(_SC_PAGE_SIZE);
    srand(atol(p[1]));
    INT pool_size = SIZE * sizeof(INT) + 2 * page_size;
    INT mask = 2 * page_size / sizeof(INT) - 1;
    
    auto ap = (INT*)malloc(SIZE * sizeof(INT) * 2);
    auto pool_0 = (INT*)malloc(pool_size);
    auto pool_1 = (INT*)malloc(pool_size);
    #if ALIGN16 == 0
        if (INT(ap) & 0xF) {
            ap += 1;
        }
    #endif
    #if ALIGN16 == 8
        if (!(INT(ap) & 0xF)) {
            ap += 1;
        }
    #endif
    
    HELLO
    unsigned i = 0, j = SIZE;
    #if ALIGN16 == 0
        if (INT(pool_0) & 0xF) {
            i = 1;
        }
    #endif
    #if ALIGN16 == 8
        if (!(INT(pool_0) & 0xF)) {
            i = 1;
        }
    #endif
    
    random_number<INT>(ap, SIZE);
    random_number<INT>(pool_0 + i, SIZE);
    random_number<INT>(pool_1 + i, SIZE);
    
    auto t = __rdtsc();
    for(unsigned k = VOLUME / 2; k--;) {
        SUBR(pool_0 + j, pool_1 + i, ap);
        SUBR(pool_1 + j, ap, pool_0 + i);
        i = (i + 2) & mask;
        j = (j + SIZE * 2) & mask;
    }
    t = __rdtsc() - t;
    auto cycles = t / VOLUME;
    j = (j + mask - 1 - SIZE * 2) & mask;
    printf("spent %lld   ticks %lld   result %lX\n", t, cycles, pool_1[j]);
    GOODBYE

    return 0;
}
