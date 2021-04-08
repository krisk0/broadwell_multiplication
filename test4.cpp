#include <cstdint>
#include <gmp.h>
#include <cassert>

#include "automagic/mpn_le_4.h"

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, 4, v, 4)
#define BAAD(r, u, v) mul4_broadwell(r, u, v)
#define SIZE 4
#define INT uint64_t
#define RAND_SEED 20190605

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
void mul4_broadwell(mp_ptr, mp_srcptr up, mp_srcptr);
}

#include "test-internal.h"

#define test_mpn_le_slave(result, u, v)      \
    {                                        \
        INT code;                            \
        mpn_le_4(code, u + 0, v + 0);        \
        assert(code == result);              \
    }

void
test_mpn_le_4() {
    INT a[4], b[4];
    memset(a + 0, 0x2, sizeof(a));
    memcpy(b + 0, a + 0, sizeof(b));
    test_mpn_le_slave(0, a, b);
    a[0] += ((INT)1) << 63;
    test_mpn_le_slave(0, a, b);
    test_mpn_le_slave(1, b, a);
    b[0] = a[0] - 0x2;
    test_mpn_le_slave(0, a, b);
    test_mpn_le_slave(1, b, a);
    // TODO: change a[1] a[2] a[3], not just a[0]
}

int main() {
    do_test();

    test_mpn_le_4();

    printf("Test passed\n");
    return 0;
}
