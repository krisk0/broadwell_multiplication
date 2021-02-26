#pragma once

#include <algorithm>
#include <immintrin.h>

#include "bordeless-alloc.h"
#include "automagic/toom22_generic_aux.h"

#if __znver2__
    #define AMD_ZEN 1
#endif

// TODO: decrease to 12 and test/benchmark
constexpr uint16_t TOOM_2X_BOUND = 28;

#define LOUD_6_LINES 0
#define SHOW_SUBROUTINE_NAME 0

// TODO: benchmark if mul_n_zen_4arg() is useful
#if defined(MUL_BASECASE_4ARG)
    #define MUL_BASECASE_SYMMETRIC(x, y, z, w) MUL_BASECASE_4ARG(x, y, z, w)
#else
    #define MUL_BASECASE_SYMMETRIC(x, y, z, w) __gmpn_mul_basecase(x, y, z, w, z)
#endif

void dump_number(const mp_limb_t* p, unsigned n);

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
mp_limb_t __gmpn_addmul_1_adox(mp_ptr, mp_srcptr, mp_size_t, mp_limb_t);
void mul_11(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_zen(mp_ptr, mp_srcptr, mp_srcptr);
void mul8_aligned(mp_ptr, mp_srcptr, mp_srcptr);
void mul7_aligned(mp_ptr, mp_srcptr, mp_srcptr);
void mul7_t03(mp_ptr, mp_srcptr, mp_srcptr);
#if AMD_ZEN
    void mul6_zen(mp_ptr, mp_srcptr, mp_srcptr);
    #define MUL6_SUBR mul6_zen
    void mul11_ryzen(mp_ptr, mp_srcptr, mp_srcptr);
    #define MUL11_SUBR mul11_ryzen
#else
    void mul6_aligned(mp_ptr, mp_srcptr, mp_srcptr);
    #define MUL6_SUBR mul6_aligned
    void mul11_bwl(mp_ptr, mp_srcptr, mp_srcptr);
    #define MUL11_SUBR mul11_bwl
#endif
void mpn_add_4k_plus2_4arg(mp_ptr, mp_limb_t, mp_srcptr, uint16_t);
mp_limb_t mpn_sub_2k_plus2_inplace(mp_ptr, mp_srcptr, uint16_t);
void mul7_2arg(mp_ptr, mp_srcptr);
void mul5_aligned(mp_ptr, mp_srcptr, mp_srcptr);
void mul3(mp_ptr, mp_srcptr, mp_srcptr);
void addmul_8x3(mp_ptr, mp_srcptr, mp_srcptr);
}

template<uint16_t> void toom22_broadwell_t(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr);
template<uint16_t> void toom22_8x_broadwell_t(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr);
template<uint16_t> constexpr uint64_t toom22_itch_broadwell_t();
/*
returns -1 if w is not a degree of two, or scratch size for toom22_generic(..., w).

Scratch size for w=16 * 2**k equals 16 * (2**(k + 1) - 1)
*/
int
toom22_deg2_itch(mp_size_t w) {
    int k = 63 - _lzcnt_u64(w);
    mp_size_t m = 1 << k;
    if (m != w) {
        return -1;
    }
    k -= 4;
    if (k < 0) {
        return 0;
    }
    return ((1 << (k+1)) - 1) << 4;
}

/*
returns scratch size for n valid for toom22_12_broadwell()

scratch size for 12 * 2**k is 12 * (2**(k + 1) - 1)
*/
int
toom22_12_itch(mp_size_t n) {
    int k = 62 - _lzcnt_u64(n);
    mp_size_t m = 3 << k;
    if (m != n) {
        return -1;
    }
    k -= 2;
    if (k < 0) {
        return 0;
    }
    return 12 * ((1 << (k+1)) - 1);
}

#define mpn_add_1_2arg(t_p, what) \
    __asm__ __volatile__ (        \
     " addq %1, (%0)\n"           \
     " jnc done%=\n"              \
     "again%=:\n"                 \
     " addq $1, 8(%0)\n"          \
     " lea 8(%0), %0\n"           \
     " jc again%=\n"              \
     "done%=:"                    \
     :"+r"(t_p)                   \
     :"r"(what)                   \
     :"memory", "cc");

// same as above, but changes at most 2 limbs
#define mpn_add_1_2arg_twice(t_p, what) \
    __asm__ __volatile__ (        \
     " addq %1, (%0)\n"           \
     " jnc done%=\n"              \
     " addq $1, 8(%0)\n"          \
     "done%=:"                    \
     :"+r"(t_p)                   \
     :"r"(what)                   \
     :"memory", "cc");

#define mpn_sub_1_2arg(t_p, what) \
    __asm__ __volatile__ (        \
     " subq %1, (%0)\n"           \
     " jnc done%=\n"              \
     "again%=:\n"                 \
     " subq $1, 8(%0)\n"          \
     " lea 8(%0), %0\n"           \
     " jc again%=\n"              \
     "done%=:"                    \
     :"+r"(t_p)                   \
     :"r"(what)                   \
     :"memory", "cc");

#define mpn_sub_1_1arg(t_p)       \
    __asm__ __volatile__ (        \
     "again%=:\n"                 \
     " subq $1, (%0)\n"           \
     " lea 8(%0), %0\n"           \
     " jc again%=\n"              \
     "done%=:"                    \
     :"+r"(t_p)                   \
     :                            \
     :"memory", "cc");

/*
memory layout: a+0 a+1 ... a+n-1 b+0 b+1 ... b+n-1
n is a multiple of 4
loops = (n >> 2) - 1
*/
uint8_t
subtract_lesser_from_bigger_n(mp_ptr tgt, mp_srcptr a, uint16_t n, uint16_t loops) {
    uint8_t less;
    auto a_tail = a + n;                      // one word past tail of a
    auto b_tail = a_tail + n;                 // one word past tail of b
    mpn_less_3arg(less, a_tail, b_tail);

    if (less) {
        mpn_sub_4k(tgt, a_tail, a, loops);
    } else {
        mpn_sub_4k(tgt, a, a_tail, loops);
    }

    return less;
}

/*
memory layout: a+0 a+1 ... a+n-1 b+0 b+1 ... b+n-1

n not a multiple of 4
*/
uint8_t
subtract_lesser_from_bigger_1x(mp_ptr tgt, mp_srcptr a, uint16_t n_arg) {
    uint64_t n = n_arg;
    uint8_t less;
    auto a_tail = a + n;                      // one limb past tail of a
    auto b_tail = a_tail + n;                 // one limb past tail of b
    mpn_less_3arg(less, a_tail, b_tail);

    if (less) {
        mpn_sub_n(tgt, a_tail, a, n);
    } else {
        mpn_sub_n(tgt, a, a_tail, n);
    }

    return less;
}

template<uint16_t N>
uint8_t
subtract_lesser_from_bigger_1x_t(mp_ptr tgt, mp_srcptr a) {
    uint64_t n = N;
    uint8_t less;
    auto a_tail = a + n;                      // one limb past tail of a
    auto b_tail = a_tail + n;                 // one limb past tail of b
    mpn_less_3arg(less, a_tail, b_tail);

    if constexpr (N == 7) {
        // this speeds up 14x14 multiplication by 8 ticks (369 instead of 377)
        if (less) {
            mpn_sub7(tgt, a_tail, a);
        } else {
            mpn_sub7(tgt, a, a_tail);
        }
    } else {
        if (less) {
            mpn_sub_n(tgt, a_tail, a, n);
        } else {
            mpn_sub_n(tgt, a, a_tail, n);
        }
    }

    return less;
}

extern "C" {
mp_limb_t
mpn_add_2_4arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l);
}

// ?slow? version of mpn_add_2_4arg(), for any n>0. TODO: benchmark it
mp_limb_t
mpn_add_2_4arg_slow(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l) {
    mp_limb_t result = 0;
    // mpn_add_4k_inplace() destroys its arguments, so make copies
    auto l_copy = l;
    auto tgt_copy = tgt;
    auto b_p = ab_p + n;
    mpn_add_4k_inplace(result, tgt, ab_p, l);
    mpn_add_4k_inplace(result, tgt_copy, b_p, l_copy);
    return result;
}

// ?slow? version of mpn_add_2_3arg(), for any n>0. TODO: benchmark
mp_limb_t
mpn_add_2_3arg_slow(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n) {
    auto result = mpn_add_n(tgt, tgt, ab_p, n);
    result += mpn_add_n(tgt, tgt, ab_p + n, n);
    return result;
}

// n even, not a multiple of 4; n >= 6
mp_limb_t
mpn_add_2_3arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n) {
    // macro mpn_add_inplace() modifiers its arguments, so make copies
    mp_limb_t carry0 = n;
    auto tgt_copy = tgt;
    mpn_add_inplace(tgt_copy, ab_p, carry0);

    // ab_p now points at b
    mp_limb_t carry1 = n;
    mpn_add_inplace(tgt, ab_p, carry1);
    return carry0 + carry1;
}

mp_limb_t
subtract_in_place_then_add_4arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l) {
    mp_limb_t result = 0;
    // macro mpn_sub_4k_inplace() destroys its arguments, so make copies
    auto l_copy = l;
    auto tgt_copy = tgt;
    auto b_p = ab_p + n;
    mpn_sub_4k_inplace(result, tgt, ab_p, l);
    mpn_add_4k_inplace(result, tgt_copy, b_p, l_copy);
    // reduce result modulo 2
    return result & 1;
}

// n even, not a multiple of 4
mp_limb_t
subtract_in_place_then_add_3arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n_arg) {
    auto n = (mp_limb_t)n_arg;
    // TODO: 16-bit counter should be faster than 64-bit?
    #if HOMEGROWN_SUB
        auto result = n;
        // save tgt for later
        auto tgt_copy = tgt;
        mpn_sub_inplace(tgt_copy, ab_p, result);
    #else
        auto result = mpn_sub_n(tgt, ab_p, tgt, n);
    #endif
    #if HOMEGROWN_SUB
        /*
        ab_p now points to b.

        Need to add modulo 2, so use ^ not +
        */
        auto add_result = n;
        mpn_add_inplace(tgt, ab_p, add_result);
        result ^= add_result;
    #else
        result ^= mpn_add_n(tgt, tgt, ab_p + n, n);
    #endif
    return result;
}

template<uint16_t N>
mp_limb_t
subtract_in_place_then_add_t(mp_ptr tgt, mp_srcptr ab_p) {
    auto n = (mp_limb_t)N;
    mp_limb_t result;
    if constexpr (((N & 3) == 2) && (N >= 6)) {
        result = mpn_sub_2k_plus2_inplace(tgt, ab_p, N / 4);
    } else {
        result = mpn_sub_n(tgt, ab_p, tgt, n);
    }
    result ^= mpn_add_n(tgt, tgt, ab_p + n, n);
    return result;
}

/*
n := 4*loops + 1
add n+1-word number t_s t_p[n-1] t_p[n-2] ... t_p[1] t_p[0] to y (of bigger length)
when propagating carry, don't worry that is goes too far
*/
void
mpn_add_4k_plus_1(mp_ptr y_p, mp_limb_t t_s, mp_srcptr t_p, uint16_t loops) {
    auto n = 4 * (loops + 1);
    auto carry_p = y_p + n;
    mpn_add_4k_inplace(t_s, y_p, t_p, loops);
    mpn_add_1_2arg(carry_p, t_s);
}

/*
add n+1-word number t_s t_p[n-1] t_p[n-2] ... t_p[1] t_p[0] to y (of bigger length)
when propagating carry, don't worry that is goes too far

n even, not a multiple of 4; 6 <= n < 2**16
*/
void
mpn_add_n_plus_1(mp_ptr y_p, mp_limb_t t_s, mp_srcptr t_p, mp_size_t n) {
    auto carry_p = y_p + n;
    mp_limb_t carry = n;
    mpn_add_inplace(y_p, t_p, carry);
    t_s += carry;
    mpn_add_1_2arg(carry_p, t_s);
}

/*
n: multiple of 4

memory layout:
               <--       b      ->  <-     a     ->
               b(n-1) ... b(1) b(0) a(n-1) ... a(0)
                                                 ^
                                                 |
                                               ab_p

g := n-word number at g_p

subroutine operation:
t := -(-1)**sign * g + a + b, t bit-length is not more than n*64 + 2
add number t to number y := b(n-1) ... b(1) a(n-1) ... a(n/2+1) a(n/2)
replace y with result of the addition

carry cannot get past senior end of number y when adding t, so it is unnecessary to check
 index range when propagating carry
*/
void
toom22_interpolate_4k(mp_ptr ab_p, mp_ptr g_p, uint8_t sign, uint16_t n) {
    mp_limb_t t_senior;
    uint16_t l = (n >> 2) - 1;                // count of loops inside mpn_add_4k()
    if (sign) {
        t_senior = mpn_add_2_4arg(g_p, ab_p, n, l);
    } else {
        t_senior = subtract_in_place_then_add_4arg(g_p, ab_p, n, l);
    }
    mpn_add_4k_plus_1(ab_p + n / 2, t_senior, g_p, l);
}

template<uint16_t N>
void
toom22_interpolate_4k_t(mp_ptr ab_p, mp_ptr g_p, uint8_t sign) {
    mp_limb_t t_senior;
    constexpr uint16_t l = (N >> 2) - 1;
    if (sign) {
        t_senior = mpn_add_2_4arg(g_p, ab_p, N, l);
    } else {
        t_senior = subtract_in_place_then_add_4arg(g_p, ab_p, N, l);
    }
    mpn_add_4k_plus_1(ab_p + N / 2, t_senior, g_p, l);
}

// n even, not a multiple of 4; 10 <= n < 2**16
void
toom22_interpolate(mp_ptr ab_p, mp_ptr g_p, uint8_t sign, mp_size_t n) {
    mp_limb_t t_senior;
    if (sign) {
        t_senior = mpn_add_2_3arg(g_p, ab_p, n);
    } else {
        t_senior = subtract_in_place_then_add_3arg(g_p, ab_p, n);
    }
    mpn_add_n_plus_1(ab_p + (n / 2), t_senior, g_p, n);
}

/*
n even, not a multiple of 4; 10 <= n < 2**16

No gain no loss, this subroutine is unused
*/
template<uint16_t N>
void
toom22_interpolate_t(mp_ptr ab_p, mp_ptr g_p, uint8_t sign) {
    mp_limb_t t_senior;
    if (sign) {
        t_senior = mpn_add_2_3arg(g_p, ab_p, N);
    } else {
        t_senior = subtract_in_place_then_add_t<N>(g_p, ab_p);
    }
    if constexpr ((N & 3) == 2) {
        mpn_add_4k_plus2_4arg(ab_p + (N / 2), t_senior, g_p, N / 4);
    } else {
        mpn_add_n_plus_1(ab_p + (N / 2), t_senior, g_p, N);
    }
}

#define USE_MUL6_RZ_MACRO 0

#if USE_MUL6_RZ_MACRO
    #include "automagic/mul6_rz.h"
#endif

void
toom22_12e_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    #if SHOW_SUBROUTINE_NAME
        printf("toom22_12e_broadwell()\n");
    #endif
    #if LOUD_6_LINES
        printf("toom22_12e_broadwell_t()\n");
        printf("a=");
        dump_number((mp_ptr)ap, 12);
        printf("b=");
        dump_number((mp_ptr)bp, 12);
    #endif
    auto sign = subtract_lesser_from_bigger_6(rp, ap, ap + 6);        // a0-a1
    sign ^= subtract_lesser_from_bigger_6(rp + 6, bp, bp + 6);        // b0-b1
    #if USE_MUL6_RZ_MACRO
    // mul6_rz_macro_wr() is faster than mul6_rz() by approximately 3.5 ticks
    // mul6_rz() is slow on Ryzen, mul6_zen() should be called
    mul6_rz_macro_wr(scratch, rp, rp + 6);
    mul6_rz_macro_wr(rp, ap, bp);
    mul6_rz_macro_wr(rp + 12, ap + 6, bp + 6);
    #else
    mul_basecase_t<6>(scratch, rp, rp + 6);                           // at -1
    mul_basecase_t<6>(rp, ap, bp);                                    // at 0
    mul_basecase_t<6>(rp + 12, ap + 6, bp + 6);                       // at infinity
    #endif
    #if LOUD_6_LINES
        printf("at -1: ");
        dump_number(scratch, 12);
        printf("at  0: ");
        dump_number(rp, 12);
        printf("at  i: ");
        dump_number(rp + 12, 12);
    #endif
    toom22_interpolate_4k_t<12>(rp, scratch, sign);
    #if LOUD_6_LINES
        printf("a*b = ");
        dump_number(rp, 24);
    #endif
}

//n = 3 * 2**k, k >= 3
void
toom22_12_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        uint16_t n) {
    #if SHOW_SUBROUTINE_NAME
        printf("toom22_deg2_broadwell(%u)\n", n);
    #endif
    auto h = n / 2;
    // for line below gcc uses 32-bit calculations, not 16-bit
    uint16_t l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    auto slave_scratch = scratch + n;
    if (h == 12) {
        toom22_12e_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_12e_broadwell(rp, slave_scratch, ap, bp);
        toom22_12e_broadwell(rp + n, slave_scratch, ap + h, bp + h);
    } else {
        toom22_12_broadwell(scratch, slave_scratch, rp, rp + h, h);    // at -1
        toom22_12_broadwell(rp, slave_scratch, ap, bp, h);             // at 0
        toom22_12_broadwell(rp + n, slave_scratch, ap + h, bp + h, h); // at infinity
    }
    toom22_interpolate_4k(rp, scratch, sign, n);
}

/*
N = 3 * 2**k, k >= 2
Size 24 time (Broadwell/Ryzen): 974/843
Size 48 time: 3204/2772
*/
template <uint16_t N>
void
toom22_12_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    static_assert(N / 12 * 12 == N);
    if constexpr (N == 12) {
        /*
        replacing toom22_12e_broadwell with __gmpn_mul_basecase() here slows it
         down on skylake
        */
        toom22_12e_broadwell(rp, scratch, ap, bp);
    } else {
        constexpr auto h = N / 2;
        constexpr uint16_t l = (h >> 2) - 1;  // count of loops inside mpn_sub_4k()
        auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);          // a0-a1
        sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);          // b0-b1
        auto slave_scratch = scratch + N;
        toom22_12_broadwell_t<h>(scratch, slave_scratch, rp, rp + h);     // at -1
        toom22_12_broadwell_t<h>(rp, slave_scratch, ap, bp);              // at 0
        toom22_12_broadwell_t<h>(rp + N, slave_scratch, ap + h, bp + h);  // at inf
        toom22_interpolate_4k_t<N>(rp, scratch, sign);
    }
}

// n: degree of two, 32 <= n < 2**16
void
toom22_deg2_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n) {
    #if SHOW_SUBROUTINE_NAME
        printf("toom22_deg2_broadwell(%u)\n", (uint16_t)n);
    #endif
    mp_size_t h = n / 2;
    uint16_t l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto slave_scratch = scratch + n;
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    #if 0
        printf("|a0-a1|=\n");
        dump_number(rp, h);
        printf("|b0-b1|=\n");
        dump_number(rp + h, h);
    #endif
    if (h < 32) {
        toom22_mul16_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_mul16_broadwell(rp, slave_scratch, ap, bp);
        toom22_mul16_broadwell(rp + n, slave_scratch, ap + h, bp + h);
    } else {
        toom22_deg2_broadwell(scratch, slave_scratch, rp, rp + h, h);       // at -1
        toom22_deg2_broadwell(rp, slave_scratch, ap, bp, h);                // at 0
        toom22_deg2_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);    // at infinity
    }
    toom22_interpolate_4k(rp, scratch, sign, n);
}

// n: degree of two, >= 8
void
toom22_deg2_broadwell_careful(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n) {
    switch (n) {
    case 8:
        mul_basecase_t<8>(rp, ap, bp);
        return;
    case 16:
        toom22_mul16_broadwell(rp, scratch, ap, bp);
        return;
    default:
        toom22_deg2_broadwell(rp, scratch, ap, bp, n);
    }
}

// N: degree of two, 16 <= N < 2**16
template <uint16_t N>
void
toom22_deg2_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N == 16) {
        toom22_mul16_broadwell(rp, scratch, ap, bp);
        return;
    } else {
        static_assert(N / 32 * 32 == N);
        constexpr auto h = N / 2;
        constexpr uint16_t l = (h >> 2) - 1;         // count of loops inside mpn_sub_4k()
        auto slave_scratch = scratch + N;
        auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);            // a0-a1
        sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);            // b0-b1
        toom22_deg2_broadwell_t<h>(scratch, slave_scratch, rp, rp + h);     // at -1
        toom22_deg2_broadwell_t<h>(rp, slave_scratch, ap, bp);              // at 0
        toom22_deg2_broadwell_t<h>(rp + N, slave_scratch, ap + h, bp + h);  // at infinity
        toom22_interpolate_4k_t<N>(rp, scratch, sign);
    }
}

void toom22_1x_broadwell(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr, uint16_t);
void toom22_8x_broadwell(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr, mp_size_t);

// n even, not a multiple of 8; 10 <= n
void
toom22_2x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    if (n == 12) {
        // toom22_12e_broadwell() should be faster
        toom22_12e_broadwell(rp, scratch, ap, bp);
        return;
    }
    #if LOUD_6_LINES
        printf("toom22_2x_broadwell(%u)\n", n);
        printf("a=");
        dump_number((mp_ptr)ap, n);
        printf("b=");
        dump_number((mp_ptr)bp, n);
    #endif
    auto h = n / 2;
    auto sign = subtract_lesser_from_bigger_1x(rp, ap, h);
    #if 0
        printf("|a0-a1| = ");
        dump_number(rp, h);
    #endif
    sign ^= subtract_lesser_from_bigger_1x(rp + h, bp, h);
    #if 0
        printf("|b0-b1| = ");
        dump_number(rp + h, h);
    #endif
    if (h < TOOM_2X_BOUND) {
        MUL_BASECASE_SYMMETRIC(scratch, rp, h, rp + h);
        MUL_BASECASE_SYMMETRIC(rp, ap, h, bp);
        MUL_BASECASE_SYMMETRIC(rp + n, ap + h, h, bp + h);
    } else {
        auto slave_scratch = scratch + n;
        if (h & 1) {
            toom22_1x_broadwell(scratch, slave_scratch, rp, rp + h, h);
            toom22_1x_broadwell(rp, slave_scratch, ap, bp, h);
            toom22_1x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
        } else {
            toom22_2x_broadwell(scratch, slave_scratch, rp, rp + h, h);
            toom22_2x_broadwell(rp, slave_scratch, ap, bp, h);
            toom22_2x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
        }
    }
    #if LOUD_6_LINES
        printf("at -1: ");
        dump_number(scratch, n);
        printf("at  0: ");
        dump_number(rp, n);
        printf("at  i: ");
        dump_number(rp + n, n);
    #endif
    if (n & 3) {
        toom22_interpolate(rp, scratch, sign, n);
    } else {
        toom22_interpolate_4k(rp, scratch, sign, n);
    }
    #if LOUD_6_LINES
        printf("a*b = ");
        dump_number(rp, 2 * n);
    #endif
}

#if defined(TOOM22_2X_BROADWELL_BENCHMARK)
unsigned long long g_t_subt, g_t_mult, g_t_intt;
#endif

/*
N even, 10 <= N

scratch size: s(2*h) = 2*h + s(h)
*/
template <uint16_t N>
void
toom22_2x_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N == 12) {
        toom22_12e_broadwell(rp, scratch, ap, bp);
    } else if constexpr (!(N & 7)) {
        toom22_8x_broadwell_t<N>(rp, scratch, ap, bp);
    } else {
        // N not 12 and does not divide by 8
        constexpr auto h = N / 2;
        #if defined(TOOM22_2X_BROADWELL_BENCHMARK)
        unsigned long long t0, t1;
        if constexpr (N == (uint16_t)TOOM22_2X_BROADWELL_BENCHMARK) {
            t0 = __rdtsc();
        }
        #endif
        auto sign = subtract_lesser_from_bigger_1x_t<h>(rp, ap);
        sign ^= subtract_lesser_from_bigger_1x_t<h>(rp + h, bp);
        #if defined(TOOM22_2X_BROADWELL_BENCHMARK)
        if constexpr (N == (uint16_t)TOOM22_2X_BROADWELL_BENCHMARK) {
            t1 = __rdtsc();
            g_t_subt += t1 - t0;
        }
        #endif
        auto slave_scratch = scratch + N;
        // tried mul7_trice() here, got slight slow-down
        if constexpr (h == 7) {
            // this optimization gave 7 ticks on Broadwell, 12 ticks on Ryzen
            mul7_2arg(scratch, rp);
        } else {
            toom22_broadwell_t<h>(scratch, slave_scratch, rp, rp + h);
        }
        toom22_broadwell_t<h>(rp, slave_scratch, ap, bp);
        toom22_broadwell_t<h>(rp + N, slave_scratch, ap + h, bp + h);
        #if defined(TOOM22_2X_BROADWELL_BENCHMARK)
        if constexpr (N == (uint16_t)TOOM22_2X_BROADWELL_BENCHMARK) {
            t0 = __rdtsc();
            g_t_mult += t0 - t1;
        }
        #endif
        if constexpr (N & 3) {
            toom22_interpolate_t<N>(rp, scratch, sign);
        } else {
            toom22_interpolate_4k_t<N>(rp, scratch, sign);
        }
        /*
        TODO: toom22_interpolate(,,,22) takes 97 ticks on Skylake and 113-117 ticks
         on Ryzen. Most other subroutines are faster on Ryzen. What's the matter?
        */
        #if defined(TOOM22_2X_BROADWELL_BENCHMARK)
        if constexpr (N == TOOM22_2X_BROADWELL_BENCHMARK) {
            g_t_intt += __rdtsc() - t0;
        }
        #endif
    }
}

void
mul_1by1(mp_ptr tgt, mp_limb_t a, mp_limb_t b) {
    mp_limb_t r0, r1;
    __asm__ __volatile__ (
        "mulx %2, %0, %1"
        : "=r"(r0), "=r"(r1)
        : "rm"(a), "d"(b)
    );
    tgt[0] = r0;
    tgt[1] = r1;
}

void
call_addmul(mp_ptr rp, mp_srcptr up, mp_limb_t v0, uint16_t n, mp_ptr tail) {
    auto senior = __gmpn_addmul_1_adox(rp, up, n, v0);
    mpn_add_1_2arg(tail, senior);
}

// n: odd, > 12
void
toom22_1x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    n -= 1;
    #if MEASURE_TIME_IN_1X_BROADWELL
        uint64_t t;
        if (n == g_0 - 1) {
            t = __rdtsc();
        }
    #endif
    if (n & 7) {
        toom22_2x_broadwell(rp, scratch, ap, bp, n);
    } else {
        toom22_8x_broadwell(rp, scratch, ap, bp, n);
    }
    #if MEASURE_TIME_IN_1X_BROADWELL
        if (n == g_0 - 1) {
            g_1 += __rdtsc() - t;
        }
    #endif
    rp += n;
    auto tail = rp + n;
    mul_1by1(tail, ap[n], bp[n]);
    #if MEASURE_TIME_IN_1X_BROADWELL
        if (n == g_0 - 1) {
            t = __rdtsc();
        }
    #endif
    /*
    benchmarking shows that two calls to __mpn_addmul_1(,,25,) cost 167 ticks,
     which means that __mpn_addmul_1() spends 3.34 tacts per limb on Skylake

    __gmpn_addmul_1() found in x86_64/mulx/adx is slightly faster, so use it instead
     of coreibwl __gmpn_addmul_1()
    */
    call_addmul(rp, ap, bp[n], n, tail);
    call_addmul(rp, bp, ap[n], n, tail);
    #if MEASURE_TIME_IN_1X_BROADWELL
        if (n == g_0 - 1) {
            g_2 += __rdtsc() - t;
        }
    #endif
}

// N: odd, not too big
// 310 ticks on Ryzen for N=13, compared to 300 for __gmpn_mul_basecase()
template<uint16_t N>
void
toom22_1x_n_minus(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    static constexpr auto n = N - 1;
    toom22_2x_broadwell_t<n>(rp, scratch, ap, bp);
    rp += n;
    auto tail = rp + n;
    mul_1by1(tail, ap[n], bp[n]);
    call_addmul(rp, ap, bp[n], n, tail);
    call_addmul(rp, bp, ap[n], n, tail);
}

namespace itch {

bool
is_power_of_2(uint64_t n) {
    return n == 1 << __tzcnt_u16(n);
}

uint16_t
sum_progression(uint16_t alpha, uint16_t betta) {
    auto l = __tzcnt_u16(betta / alpha) + 1;
    return alpha * ((1 << l) - 1);
}

template <uint16_t N>
constexpr uint64_t
toom22_broadwell_inexact_t() {
    if constexpr (N < 12) {
        return 0;
    }
    constexpr auto h = (N + 1) / 2;
    return toom22_broadwell_inexact_t<h>() + 2 * h;
}

template<uint16_t n>
constexpr uint16_t
log2() {
    return (n <= 1) ? 0 : 1 + log2<n / 2>();
}

template<uint16_t n>
constexpr uint16_t
two_power() {
    return (n == 1) ? 2 : 2 * two_power<n - 1>();
}

template<>
constexpr uint16_t
two_power<0>() {
    return 1;
}

template<uint16_t n>
constexpr bool
is_power_of_2_t() {
    constexpr auto l = log2<n>();
    return n == two_power<l>();
}

template<uint16_t alpha, uint16_t betta>
constexpr uint64_t
sum_progression_t() {
    constexpr auto l = log2<betta / alpha>() + 1;
    return alpha * (two_power<l>() - 1);
}

template<int16_t N, int16_t K>
struct toom22_broadwell_t {
    static constexpr uint64_t v() {
        constexpr int16_t h = (N + 1) / 2;
        if constexpr ((N & 1) == 0) {
            return 2 * h + toom22_broadwell_t<h, K - 1>::v();
        }
        constexpr auto r0 = toom22_broadwell_t<h, K - 1>::v();
        constexpr auto r1 = toom22_broadwell_t<h - 1, K - 1>::v();
        return r0 > r1 ? 2 * h + r0 : 2 * h + r1;
    };
};

template<int16_t N>
struct toom22_broadwell_t<N, 0> {
    static constexpr uint64_t v() {
        // return zero, unless degree of two or good multiple of 12,
        constexpr uint16_t M = N / 12;
        if constexpr ((M * 12 == N) && (is_power_of_2_t<M>())) {
            return sum_progression_t<12, N>();
        }
        if constexpr (is_power_of_2_t<(uint16_t)N>() && (N >= 16)) {
            return sum_progression_t<16, N>();
        }
        // ... or exactly TOOM_2X_BOUND
        return N < TOOM_2X_BOUND ? 0 : (N + 1) / 2 * 2;
    }
};

template<uint16_t> constexpr uint64_t toom22_forced_t();

template<uint16_t A, uint16_t B>
struct toom22_forced_struct {
    static constexpr uint64_t v() {
         constexpr auto x = toom22_forced_t<A>();
         constexpr auto y = toom22_forced_struct<A + 1, B>::v();
         return x > y ? x : y;
    }
};

template<uint16_t N>
struct toom22_forced_struct<N, N> {
    static constexpr uint64_t v() { return toom22_forced_t<N>(); }
};

template<uint16_t A, uint16_t B>
struct toom22_broadwell_struct {
    static constexpr uint64_t v() {
         constexpr auto x = toom22_itch_broadwell_t<A>();
         constexpr auto y = toom22_broadwell_struct<A + 1, B>::v();
         return x > y ? x : y;
    }
};

template<uint16_t N>
struct toom22_broadwell_struct<N, N> {
    static constexpr uint64_t v() { return toom22_itch_broadwell_t<N>(); }
};

// Itch size for forced call of toom22_2x_broadwell_t<N> or toom22_1x_broadwell_t<N>
template<uint16_t N>
constexpr uint64_t
toom22_forced_t() {
    constexpr auto h = (N + 1) / 2;
    if constexpr(N & 1) {
        constexpr auto b0 = toom22_itch_broadwell_t<h>();
        constexpr auto b1 = toom22_itch_broadwell_t<h - 1>();
        return 2 * h + (b0 > b1 ? b0 : b1);
    } else {
        return N + toom22_itch_broadwell_t<h>();
    }
}

// maximum of toom22_forced_t<>() over range A..B
template<uint16_t A, uint16_t B>
constexpr uint64_t
toom22_forced_t_2arg() {
    return toom22_forced_struct<A, B>::v();
}

// maximum of toom22_itch_broadwell_t<>() over range A..B
template<uint16_t A, uint16_t B>
constexpr uint64_t
toom22_broadwell_t_2arg() {
    return toom22_broadwell_struct<A, B>::v();
}

// upper bound for calls of any toom22* over range A..B
template<uint16_t A, uint16_t B>
constexpr uint64_t
toom22_whatever_t() {
    constexpr auto x = toom22_forced_t_2arg<A, B>();
    constexpr auto y = toom22_broadwell_t_2arg<A, B>();
    return x > y ? x : y;
}

} // namespace itch

// n: multiple of 8, 16 <= n <= 2**15; zeroes = count of junior zeroes in n
void
toom22_8x_broadwell_6arg(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        uint16_t n, uint16_t zeroes) {
    auto h = n / 2;
    uint16_t l = (h >> 2) - 1;                  // count of loops inside mpn_sub_4k()
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    if (h < TOOM_2X_BOUND) {
        MUL_BASECASE_SYMMETRIC(scratch, rp, h, rp + h);               // at -1
        MUL_BASECASE_SYMMETRIC(rp, ap, h, bp);                        // at 0
        MUL_BASECASE_SYMMETRIC(rp + n, ap + h, h, bp + h);            // at infinity
    } else {
        auto slave_scratch = scratch + n;
        if (zeroes >= 4) {
            toom22_8x_broadwell(scratch, slave_scratch, rp, rp + h, h);
            toom22_8x_broadwell(rp, slave_scratch, ap, bp, h);
            toom22_8x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
        } else {
            toom22_2x_broadwell(scratch, slave_scratch, rp, rp + h, h);
            toom22_2x_broadwell(rp, slave_scratch, ap, bp, h);
            toom22_2x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
        }
    }
    toom22_interpolate_4k(rp, scratch, sign, n);
}

// N: multiple of 8, 16 <= N
template <uint16_t N>
void
toom22_8x_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    if constexpr ((N / 24 * 24 == N) && (itch::is_power_of_2_t<N / 24>())) {
        toom22_12_broadwell_t<N>(rp, scratch, ap, bp);
    } else if constexpr (itch::is_power_of_2_t<N>() && (N >= 16)) {
        toom22_deg2_broadwell_t<N>(rp, scratch, ap, bp);
    } else {
        constexpr auto h = N / 2;
        constexpr auto l = h / 4 - 1;
        auto slave_scratch = scratch + N;
        auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);            // a0-a1
        sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);            // b0-b1
        toom22_broadwell_t<h>(scratch, slave_scratch, rp, rp + h);
        toom22_broadwell_t<h>(rp, slave_scratch, ap, bp);
        toom22_broadwell_t<h>(rp + N, slave_scratch, ap + h, bp + h);
        toom22_interpolate_4k_t<N>(rp, scratch, sign);
    }
}

/*
n: multiple of 8, 16 <= n < 2**16;

scratch: enough for any subroutine that might be called
*/
void
toom22_8x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n_arg) {
    // compiler generates stupid code because mp_size_t is signed, so we convert type
    auto n = (uint16_t)n_arg;
    #if SHOW_SUBROUTINE_NAME
        printf("toom22_8x_broadwell(%u)\n", n);
    #endif
    // remove junior zeroes, see what is left
    auto zeroes = __tzcnt_u16(n);
    uint16_t unzeroed = n >> zeroes;   // compiler uses 32-bit register for unzeroed
    switch (unzeroed) {
    case 1:
        toom22_deg2_broadwell_careful(rp, scratch, ap, bp, n_arg);
        return;
    case 3:
        toom22_12_broadwell(rp, scratch, ap, bp, n);
        return;
    }
    toom22_8x_broadwell_6arg(rp, scratch, ap, bp, n, zeroes);
}

// Convenience procedure, n >= 12
void
toom22_xx_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    auto zeroes = __tzcnt_u16(n);
    switch (zeroes) {
    case 0:
        toom22_1x_broadwell(rp, scratch, ap, bp, n);
        return;
    case 1: [[fallthrough]];
    case 2:
        toom22_2x_broadwell(rp, scratch, ap, bp, n);
        return;
    }
    uint16_t unzeroed = n >> zeroes;
    switch (unzeroed) {
    case 1:
        toom22_deg2_broadwell_careful(rp, scratch, ap, bp, n);
        return;
    case 3:
        switch (zeroes) {
        case 3:
            toom22_12_broadwell_t<24>(rp, scratch, ap, bp);
            return;
        case 4:
            toom22_12_broadwell_t<48>(rp, scratch, ap, bp);
            return;
        case 5:
            toom22_12_broadwell_t<96>(rp, scratch, ap, bp);
            return;
        }
        toom22_12_broadwell(rp, scratch, ap, bp, n);
        return;
    }
    toom22_8x_broadwell_6arg(rp, scratch, ap, bp, n, zeroes);
}

#if 0
Formulas and algorithm of Toom-Cook-2/2 for odd n

n = 2 * h + 1
t = 2**(64 * h)
q = 2**(64 * (h-1))
a = a1 * t + a0
b = b1 * t + b0
a1 < 2**(64 * q)
a0 < t
b1 < 2**(64 * q)
b0 < t

v1 = (a1-a0)*(b1-b0)
v0 = a0 * b0
v2 = a1 * b1
v3 = v2 + v0 - v1     0 <= v3 < 2**(64 * 2 * h)

|v1| < t**2
v0 < t**2
v2 < q**2

v1: 2*h temp, 2*h result   + scratch(h)       3*h + scratch(h)
v0: 2*h                    + scratch(h)
v2: 2*(h-1)                + scratch(h-1)
v3: fits in 2*h

m1 = h + 2*h + scratch(h)
     \      \
      \      v1
       one of two subtraction results
m0 = 2*h + scratch(h)
      \
       \
        \
         v1
m2 = 2*h + scratch(h-1)
      \
       \
        v1

s(x) = 0, x<12
s(2*h) = 2 * h + s(h)
s(2*h+1) = max(m1, m0, m2)
m1 > m0
s(2*h+1) = max(m1, m2) = max(3*h+s(h), 2*h+s(h-1))


a*b = (a1*t + a0) * (b1*t + b0) = t**2 * v2 + v0 + t*(a1*b0 + a0*b1)

v1 = v2 + v0 - (a1*b0 + a0*b1) >= 0

a*b = t**2 * v2 + v0 + t*(v2 + v0 - v1)

v3 = v2 + v0 - v1
0 <= v3 <= 2*((t-1)*(q-1)) < 2 * t * q      (h + h - 1 plus 1 bit <= 2*h limbs)

count v1, v0, v2, v3, a*b
v1 at scratch
v0 at rp + 0
v2 at rp + 2*h
v3 at scratch + 0
a1-a0 at scratch + 2*h
temp when calculating v1 at scratch + 3*h (of size s(h))
temp when calculating v2 at scratch + 2*h (of size s(h-1))
#endif

namespace toom22_1x {

/*
q = h - 1

memory layout: u+0 u+1 ... u+h-1 w+0 w+1 ... w+q-1
                |
                |
                a_p

count abs(u-w), place it at tgt
return sign: 0 if u-w >= 0, else 1

h >= TOOM_2X_BOUND / 2
*/

template <uint16_t N>
void
mpn_sub_t(mp_ptr rp, mp_srcptr ap, mp_srcptr bp) {
    if constexpr ((N > 4) && (0 == (N & 3))) {
        uint16_t l = (N / 4) - 1;
        mpn_sub_4k(rp, ap, bp, l);
    } else {
        if constexpr (N == 6) {
            mpn_sub6(rp, ap, bp);
        }
        else {
            mpn_sub_n(rp, ap, bp, N);
        }
    }
}

template<uint16_t h, uint16_t q>
void
subtract_longer_from_shorter(mp_ptr tgt, mp_srcptr a_p) {
    if constexpr (h == 6) {
        // gain 7 ticks on Broadwell, 3 ticks on Ryzen for toom22_broadwell_t<11>
        subtract_longer_from_shorter_6(tgt, a_p);
    } else if constexpr (h == 7) {
        /*
        this optimization speeds up toom22_broadwell_t<13>() by 14 ticks on Ryzen
         (from 308 to 294)
        */
        subtract_longer_from_shorter_7(tgt, a_p);
    } else if constexpr (h == 8) {
        // 1 tick on Broadwell, 4 ticks on Ryzen for toom22_broadwell_t<15>()
        subtract_longer_from_shorter_8(tgt, a_p);
    } else {
        auto borrow = mpn_sub_n(tgt, a_p, a_p + h, q);
        tgt[q] = a_p[q] - borrow;
    }
}

template<uint16_t h, uint16_t q>
uint8_t
subtract_lesser_from_bigger(mp_ptr tgt, mp_srcptr a_p) {
    if (a_p[q]) {
        subtract_longer_from_shorter<h, q>(tgt, a_p);
        return 0;
    }
    /*
    u senior limb is zero, result will be 1 limb shorter than expected

    memory layout: u+0 u+1 ... u+q-1 0 w+0 w+1 ... w+q-1

    if u >= w, subtract w from u and return 0
    else subtract u from w and return 1
    */
    uint8_t result;
    auto w_head = a_p + h;                      // head of w
    auto w_tail = a_p + (q + h);                // one past tail of w
    uint8_t less;

    mpn_less_3arg_hole(less, w_head, w_tail);
    if (less) {
        mpn_sub_t<q>(tgt, w_head, a_p);
    } else {
        mpn_sub_t<q>(tgt, a_p, w_head);
    }
    tgt[q] = 0;

    return less;
}

template <uint16_t h, uint16_t q>
uint8_t
v1(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    // place one subtraction result at rp + h
    auto sign = subtract_lesser_from_bigger<h, q>(rp + h, ap);
    // place another subtraction result at rp
    sign ^= subtract_lesser_from_bigger<h, q>(rp, bp);
    if constexpr (h == 7) {
        // gain 7 ticks on Broadwell, 2 on Ryzen
        mul7_2arg(scratch, rp);
    } else {
        toom22_broadwell_t<h>(scratch, scratch + 2*h, rp + h, rp);
    }
    return sign;
}

template<uint16_t N>
mp_limb_t
mpn_add_inplace_t(mp_ptr rp, mp_ptr ap) {
    if constexpr (((N & 3) == 0) && (N >= 8)) {
        mp_limb_t carry = 0;
        auto loop_count = N / 4 - 1;
        mpn_add_4k_inplace(carry, rp, ap, loop_count);
        return carry;
    } else {
        return mpn_add_n(rp, rp, ap, N);
    }
}

template<uint16_t N>
void
mpn_sub_inplace_t(mp_ptr rp, mp_ptr ap) {
    if constexpr ((N / 4 * 4 == N) && (N >= 8)) {
        // 1 tick speedup for N=12 => 1 tick speedup of toom22_broadwell_t<13>()
        auto loop_count = N / 4 - 1;
        auto ap_copy = ap, rp_copy = rp;
        // TODO: can catch another tick or two
        mpn_sub_4k(rp, ap_copy, rp_copy, loop_count);
    } else {
        (void)mpn_sub_n(rp, ap, rp, N);
    }
}

/*
|v1| of size 2*h at scratch + 0
v0 of size 2*h at rp + 0
v2 of size 2*q at rp + 2 * h

do Toom22 interpolation:
v3 = v2 + v0 - v1           2*h limbs
add 2*h-limb v3 to number at rp + h

v3 is known to fit 2*h limbs, which means that limb at index 2*h need not be cared
 for. For instance, carry from limb at index 2*h-1 should be discarded when
 calculating v3 = v2 + v0 + |v1|.
*/

template <uint16_t h, uint16_t q>
void
interpolate(mp_ptr rp, mp_ptr scratch, uint8_t v1_sign) {
    if (v1_sign) {
        // v3 = |v1| + v0 + v2
        (void)mpn_add_inplace_t<2 * h>(scratch, rp);
    } else {
        // v3 = v0 - |v1| + v2
        (void)mpn_sub_inplace_t<2 * h>(scratch, rp);
    }
    // v2 is 2 limbs shorter, need to spread carry
    auto carry = mpn_add_inplace_t<2 * q>(scratch, rp + 2 * h);
    auto here = scratch + 2 * q;
    // TODO: can spread carry inside assembler macro
    mpn_add_1_2arg_twice(here, carry);
    // v3 stored at scratch
    here = rp + h;
    carry = mpn_add_inplace_t<2 * h>(here, scratch);
    here = rp + 3 * h;
    // no worry of carry going too far, if caller allocated enough space at rp
    mpn_add_1_2arg(here, carry);
}

} // end namespace toom22_1x

// Good bound on itch size for N < 8 * TOOM_2X_BOUND, inexact bound for larger N
template<uint16_t N>
constexpr uint64_t
toom22_itch_broadwell_t() {
    static_assert(TOOM_2X_BOUND >= 12);
    if constexpr (N < 1 * TOOM_2X_BOUND) {
        return itch::toom22_broadwell_t<N, 0>::v();
    }
    if constexpr (N < 2 * TOOM_2X_BOUND) {
        return itch::toom22_broadwell_t<N, 1>::v();
    }
    if constexpr (N < 4 * TOOM_2X_BOUND) {
        return itch::toom22_broadwell_t<N, 2>::v();
    }
    if constexpr (N < 8 * TOOM_2X_BOUND) {
        return itch::toom22_broadwell_t<N, 3>::v();
    }
    return itch::toom22_broadwell_inexact_t<N>();
}

// Good bound on itch size, non-constexpr form
uint64_t
toom22_itch_broadwell(uint16_t N) {
    if (N < 12) {
        return 0;
    }
    // special care for proper multiple of 12, and degree of two
    if ((N / 12 * 12 == N) && (itch::is_power_of_2(N / 12))) {
        return itch::sum_progression(12, N);
    }
    if (itch::is_power_of_2(N) && (N >= 16)) {
        return itch::sum_progression(16, N);
    }
    if (N < TOOM_2X_BOUND) {
        return 0;
    }
    if (!(N & 1)) {
        return N + toom22_itch_broadwell(N / 2);
    }
    auto h = (N + 1)/ 2;
    return 2 * h + std::max(toom22_itch_broadwell(h), toom22_itch_broadwell(h - 1));
}

// N: odd, >= TOOM_2X_BOUND
template <uint16_t N>
void
toom22_1x_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    constexpr auto h = (N + 1) / 2;
    constexpr auto q = h - 1;
    #if LOUD_6_LINES
    if constexpr ((N == 13) || (N == 25)) {
        printf("toom22_1x_broadwell_t(%u)\n", N);
        printf("a=");
        dump_number((mp_ptr)ap, N);
        printf("b=");
        dump_number((mp_ptr)bp, N);
    }
    #endif
    auto v1_sign = toom22_1x::v1<h, q>(rp, scratch, ap, bp);   // |v1| at scratch + 0
    toom22_broadwell_t<h>(rp, scratch + 2 * h, ap, bp);        // v0 at rp + 0
    toom22_broadwell_t<q>(rp + 2 * h, scratch + 2 * h, ap + h, bp + h);
                                                               // v2 at rp + 2*h
    #if LOUD_6_LINES
    if constexpr ((N == 13) || (N == 25)) {
        printf("at -1: ");
        dump_number(scratch, 2 * h);
        printf("at  0: ");
        dump_number(rp, 2 * h);
        printf("at  i: ");
        dump_number(rp + 2 * h, 2 * q);
    }
    #endif
    toom22_1x::interpolate<h, q>(rp, scratch, v1_sign);
    #if LOUD_6_LINES
    if constexpr ((N == 13) || (N == 25)) {
        printf("a*b = ");
        dump_number(rp, 2 * N);
    }
    #endif
}

void
addmul_8x3_slow(mp_ptr rp, mp_srcptr ap, mp_srcptr bp) {
    mp_limb_t scratch[11];
    mpn_mul(scratch, ap, 8, bp, 3);
    auto carry = mpn_add_n(rp, rp, scratch, 11);
    rp += 11;
    mpn_add_1_2arg(rp, carry);
}

/*
239 ticks on Broadwell, 4 ticks faster than __gmpn_mul_basecase(11)
215 ticks on Ryzen, 2 ticks slower than __gmpn_mul_basecase(11)
*/
void
mul_11(mp_ptr rp, mp_srcptr ap, mp_srcptr bp) {
    mul_basecase_t<8>(rp, ap, bp);
    rp += 8;
    mul_basecase_t<3>(rp + 8, ap + 8, bp + 8);
    addmul_8x3(rp, ap, bp + 8);
    addmul_8x3(rp, bp, ap + 8);
}

template <uint16_t N, bool fear_of_page_break>
void
mul_basecase_t(mp_ptr rp, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N == 13) {
        /*
        TODO: reduce TOOM_2X_BOUND to 12, then remove toom22_1x_broadwell_t<13>()
         call below
        */
        // toom22_1x_broadwell_t<13>() is slightly faster than __gmpn_mul_basecase()
        mp_limb_t scratch[itch::toom22_forced_t<13>()];
        toom22_1x_broadwell_t<N>(rp, scratch, ap, bp);
        // use hand-optimized subroutine if possible
    } else if constexpr (N == 11) {
        MUL11_SUBR(rp, ap, bp);
    } else if constexpr (N == 8) {
        if constexpr(fear_of_page_break) {
            // 2 ticks slower than mul8_zen on Ryzen, same time on Skylake
            mul8_aligned(rp, ap, bp);
        } else {
            mul8_zen(rp, ap, bp);
        }
    } else if constexpr (N == 7) {
        if constexpr(fear_of_page_break) {
            mul7_aligned(rp, ap, bp);
        } else {
            /*
            call of mul7_t03() instead of MUL_BASECASE_SYMMETRIC() speeds up
             toom22_1x_broadwell_t<13>() by 30 ticks on Skylake
            */
            mul7_t03(rp, ap, bp);
        }
    } else if constexpr (N == 6) {
        MUL6_SUBR(rp, ap, bp);
    } else if constexpr (N == 5) {
        /*
        gain 20 ticks on Broadwell, 11 ticks on Ryzen for 11x11 Toom22 multiplication
        */
        mul5_aligned(rp, ap, bp);
    } else if constexpr (N == 3) {
        mul3(rp, ap, bp);
    }
    else {
        // call asm subroutine from GMP or something very similar
        MUL_BASECASE_SYMMETRIC(rp, ap, N, bp);
    }
}

template<uint16_t N>
void
force_call_toom22_broadwell(mp_ptr rp, mp_ptr scr, mp_srcptr ap, mp_srcptr bp) {
    if constexpr(N & 1) {
        toom22_1x_broadwell_t<N>(rp, scr, ap, bp);
    } else {
        toom22_2x_broadwell_t<N>(rp, scr, ap, bp);
    }
}

// N: integer, not very big
template<uint16_t N>
void
toom22_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    #if SHOW_SUBROUTINE_NAME
        printf("toom22_broadwell_t<%u>\n", N);
    #endif
    if constexpr (N < TOOM_2X_BOUND) {
        // for some N, call Toom-22 subroutine even though N is small
        if constexpr ((N / 12 * 12 == N) && (itch::is_power_of_2_t<N / 12>())) {
            // toom22_2x_broadwell_t is smart enough
            toom22_2x_broadwell_t<N>(rp, scratch, ap, bp);
        } else if constexpr (itch::is_power_of_2_t<N>() && (N >= 16)) {
            toom22_2x_broadwell_t<N>(rp, scratch, ap, bp);
        } else {
            mul_basecase_t<N>(rp, ap, bp);
        }
    } else {
        force_call_toom22_broadwell<N>(rp, scratch, ap, bp);
    }
}
