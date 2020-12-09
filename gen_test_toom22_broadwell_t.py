"""
test subroutines toom22_1x_broadwell_t<N> and toom22_2x_broadwell_t<N>() for a
 range of N

TODO: instead of generating code with repeated patterns, use loop over constexpr
"""

g_head = r'''
// This file auto-generated from @me

#include "toom22_generic.h"

#include "test-internal.h"

#define MIN_N @min
#define MAX_N @max
constexpr auto SCRATCH_SIZE = itch::toom22_whatever_t<MIN_N, MAX_N>();
#define RAND_SEED 20190725

INT* g_scratch;
INT g_a[MAX_N];
INT g_b[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];
INT g_page_mask;
INT g_page_unmask;

#define NS(x)                                                                       \
    namespace _ ## x {                                                              \
    constexpr uint16_t SIZE = x;                                                    \
                                                                                    \
    void call_good() {                                                              \
        mpn_mul_n(g_result_good + 0, g_a + 0, g_b + 0, SIZE);                       \
    }                                                                               \
                                                                                    \
    void call_baad() {                                                              \
        force_call_toom22_broadwell<SIZE>(g_result_baad + 0, g_scratch, g_a + 0,    \
                g_b + 0);                                                           \
    }
'''

g_piece = '''
NS(%s)
#include "test-toom22_generic-internal.h"
}
'''

g_main = r'''
int
main() {
    bordeless_alloc_prepare(g_page_mask, g_page_unmask);
    bordeless_alloc_nodefine(INT, g_scratch, SCRATCH_SIZE * sizeof(INT), g_page_mask, g_page_unmask);
    
%s

    printf("Test passed\n");
    return 0;
}
'''

import os, sys

g_min_n = int(os.getenv('min_n', 10))
g_max_n = int(os.getenv('max_n', 51))

def do_it(o):
    global g_max_n
    o.write(g_head.lstrip().replace('@me', os.path.basename(sys.argv[0])).\
        replace('@max', str(g_max_n)).replace('@min', str(g_min_n)))
    g_max_n += 1
    for i in range(g_min_n, g_max_n):
        o.write(g_piece % i)
    test_calls = ['    _%s::test();' % i for i in range(g_min_n, g_max_n)]
    o.write(g_main % '\n'.join(test_calls))

with open(sys.argv[1], 'wb') as g_o:
    do_it(g_o)
