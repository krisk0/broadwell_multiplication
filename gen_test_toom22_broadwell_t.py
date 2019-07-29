"""
test subroutine toom22_broadwell_t<N>() for a range of N

348 in code below is maximal scratch size, which is scratch size for
 toom22_broadwell_t<127>() and also max scratch size for any N in range 12..128
 
TODO: instead of generating code with repeated patterns, use loop over constexpr, like

http://spraetor.github.io/2015/12/26/compile-time-loops.html

https://nilsdeppe.com/posts/for-constexpr

Relevant code on spraetor.github.io:
    template <int I, int N>
    struct Print {
      static void run() {
        std::cout << "Fibo<" << I << ">::value = " << Fibo<I>::value << "n";
        Print<I+1,N>::run();
      }
    };
    
    template <int N>
    struct Print<N,N> { static void run() {} };
"""

g_head = r'''
// This file auto-generated from @me

#include "toom22_generic.h"

#include "test-internal.h"

#define MAX_N @
#define SCRATCH_SIZE 348
#define RAND_SEED 20190725

INT* g_scratch;
INT g_a[MAX_N];
INT g_b[MAX_N];
INT g_result_good[2 * MAX_N];
INT g_result_baad[2 * MAX_N];
INT g_page_mask;
INT g_page_unmask;

#define NS(x)                                                                        \
    namespace _ ## x {                                                               \
    constexpr uint16_t SIZE = x;                                                     \
                                                                                     \
    void call_good() {                                                               \
        mpn_mul_n(g_result_good + 0, g_a + 0, g_b + 0, SIZE);                        \
    }                                                                                \
                                                                                     \
    void call_baad() {                                                               \
        toom22_broadwell_t<SIZE>(g_result_baad + 0, g_scratch, g_a + 0, g_b + 0);    \
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

g_min_n = 12
g_max_n = int(os.getenv('max_n', 51))

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

def do_it(o):
    global g_max_n
    o.write(g_head.lstrip().replace('@me', os.path.basename(sys.argv[0])).\
        replace('@', str(g_max_n)))
    g_max_n += 1
    for i in range(g_min_n, g_max_n):
        o.write(g_piece % i)
    test_calls = ['    _%s::test();' % i for i in range(g_min_n, g_max_n)]
    o.write(g_main % '\n'.join(test_calls))

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
