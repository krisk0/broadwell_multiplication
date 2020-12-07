#include <cstdint>

#include <gmp.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr, mp_size_t, mp_srcptr, mp_size_t);
void mul8_zen(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_broadwell_125(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_skylake(mp_ptr, mp_srcptr, mp_srcptr);
}

#define GOOD(r, u, v) __gmpn_mul_basecase(r, u, 8, v, 8)
#define SIZE 8
#define RAND_SEED 20190610

#if ZEN
    #define BAAD(r, u, v) mul8_zen(r, u, v)
#elif STORE1
    #include "automagic/mul8_store_once.h"
    #define BAAD(r, u, v) mul8_broadwell_store_once_wr(r, u, v)
#elif SKYLAKE
    #define BAAD(r, u, v) mul8_skylake(r, u, v)
#else
    #define BAAD(r, u, v) mul8_broadwell_125(r, u, v)
#endif

#include "test-internal.h"

int
main() {
    do_test();

    printf("Test passed\n");
    return 0;
}
