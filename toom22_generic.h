#include <immintrin.h>

extern "C" {
void __gmpn_mul_basecase(mp_ptr, mp_srcptr up, mp_size_t, mp_srcptr, mp_size_t);
mp_limb_t __mpn_addmul_1(mp_ptr, mp_srcptr, mp_size_t, mp_limb_t);
}

/*
returns -1 if w is not a degree of two, or scratch size for toom22_generic(..., w).

Scratch size for w=16 * 2**k equals 16 * (2**(k + 1) - 1)
*/
int
toom22_generic_itch(mp_size_t w) {
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

// memory layout: a+0 a+1 ... a+n-1 b+0 b+1 ... a+n-1,   loops = (n >> 2) - 1
uint8_t
subtract_lesser_from_bigger_n(mp_ptr tgt, mp_srcptr a, mp_size_t n, uint16_t loops) {
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

// n: not a multiple of 4, a >= b
void
mpn_sub_1x(mp_ptr rp, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    uint8_t s = n & 3;                        // s > 0
    auto m = n - s;                           // m < n, m: multiple of 4
    auto loops = (m >> 2) - 1;
    auto rp_shftd = rp + s;
    auto ap_shftd = ap + s;
    auto bp_shftd = bp + s;
    mpn_sub_4k(rp_shftd, ap_shftd, bp_shftd, loops);    // subtraction result non-negative
    mpn_sub_n_small(rp, ap, bp, s);
    if (s) {
        mpn_sub_1_1arg(rp_shftd);
    }
}

// memory layout: a+0 a+1 ... a+n-1 b+0 b+1 ... a+n-1, n: not a multiple of 4
uint8_t
subtract_lesser_from_bigger_1x(mp_ptr tgt, mp_srcptr a, uint16_t n) {
    uint8_t less;
    auto a_tail = a + n;                      // one limb past tail of a
    auto b_tail = a_tail + n;                 // one limb past tail of b
    mpn_less_3arg(less, a_tail, b_tail);

    if (less) {
        mpn_sub_1x(tgt, a_tail, a, n);
    } else {
        mpn_sub_1x(tgt, a, a_tail, n);
    }

    return less;
}

extern "C" {
mp_limb_t
mpn_add_2_4arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l);
}

// ?slow? version of mpn_add_2_4arg(). TODO: benchmark it
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

mp_limb_t
mpn_add_2_3arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n) {
    auto result = mpn_add_n(tgt, tgt, ab_p, n);
    result += mpn_add_n(tgt, tgt, ab_p + n, n);
    return result;
}

mp_limb_t
subtract_in_place_then_add_4arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l) {
    mp_limb_t result = 0;
    // mpn_sub_4k_inplace() destroys its arguments, so make copies
    auto l_copy = l;
    auto tgt_copy = tgt;
    auto b_p = ab_p + n;
    mpn_sub_4k_inplace(result, tgt, ab_p, l);
    mpn_add_4k_inplace(result, tgt_copy, b_p, l_copy);
    // reduce result modulo 2
    return result & 1;
}

#if 0
// n: even, not a multiple of 4, >4
mp_limb_t
subtract_in_place_then_add_3arg(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n) {
    mp_limb_t result = n;
    // save tgt for later
    auto tgt_copy = tgt;
    mpn_sub_inplace(tgt_copy, ab_p, result);
    // ab_p now points to b
    result += mpn_add_n(tgt, tgt, ab_p, n);
    return result;
}
#endif

/*
n := 4*loops + 1
add n+1-word number t_s t_p[n-1] t_p[n-2] ... t_p[1] t_p[0] to y (of bigger length)
when propagating carry, don't worry that is goes too far
*/
void
mpn_add_4x_plus_1(mp_ptr y_p, mp_limb_t t_s, mp_srcptr t_p, uint16_t loops) {
    auto n = 4 * (loops + 1);
    auto carry_p = y_p + n;
    mpn_add_4k_inplace(t_s, y_p, t_p, loops);
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
toom22_deg2_interpolate_4x(mp_ptr ab_p, mp_ptr g_p, uint8_t sign, mp_size_t n) {
    mp_limb_t t_senior;
    uint16_t l = (n >> 2) - 1;                // count of loops inside mpn_add_4k()
    #if 0
        printf("sign=%d vm1=\n", sign);
        dump_number(g_p, n);
        printf("v0=\n");
        dump_number(ab_p, n);
        printf("vinf=\n");
        dump_number(ab_p + n, n);
    #endif
    if (sign) {
        t_senior = mpn_add_2_4arg(g_p, ab_p, n, l);
    } else {
        t_senior = subtract_in_place_then_add_4arg(g_p, ab_p, n, l);
    }
    mpn_add_4x_plus_1(ab_p + (n / 2), t_senior, g_p, l);
}

#if 0
// n: even, not a multiple of 4
void
toom22_deg2_interpolate(mp_ptr ab_p, mp_ptr g_p, uint8_t sign, mp_size_t n) {
    mp_limb_t t_senior;
    if (sign) {
        t_senior = mpn_add_2_3arg(g_p, ab_p, n);
    } else {
        t_senior = subtract_in_place_then_add_3arg(g_p, ab_p, n);
    }
    mpn_add_n_plus_1(ab_p + (n / 2), t_senior, g_p, n);
}
#endif

#if defined(mul6_broadwell_wr)
void
toom22_12e_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    auto sign = subtract_lesser_from_bigger_6(rp, ap, ap + 6);        // a0-a1
    sign ^= subtract_lesser_from_bigger_6(rp + 6, bp, bp + 6);        // b0-b1
    mul6_broadwell_wr(scratch, rp, rp + 6);                           // at -1
    mul6_broadwell_wr(rp, ap, bp);                                    // at 0
    mul6_broadwell_wr(rp + 12, ap + 6, bp + 6);                       // at infinity
    toom22_deg2_interpolate_4x(rp, scratch, sign, 12);
}

// n = 3 * 2**k, k >= 3, n <= 2**16
void
toom22_12_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n) {
    auto h = n / 2;
    uint16_t l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    auto slave_scratch = scratch + n;
    if (h == 12) {
        toom22_12e_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_12e_broadwell(rp, slave_scratch, ap, bp);
        toom22_12e_broadwell(rp + n, slave_scratch, ap + h, bp + h);
    } else {
        toom22_12_broadwell(scratch, slave_scratch, rp, rp + h, h);       // at -1
        toom22_12_broadwell(rp, slave_scratch, ap, bp, h);                // at 0
        toom22_12_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);    // at infinity
    }
    toom22_deg2_interpolate_4x(rp, scratch, sign, n);
}

// N = 3 * 2**k, k >= 2
template <uint16_t N>
void
toom22_12_broadwell_n(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N == 12) {
        toom22_12e_broadwell(rp, scratch, ap, bp);
        return;
    }
    constexpr auto h = N / 2;
    constexpr auto l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);              // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);              // b0-b1
    auto slave_scratch = scratch + N;
    if constexpr (h == 12) {
        toom22_12e_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_12e_broadwell(rp, slave_scratch, ap, bp);
        toom22_12e_broadwell(rp + N, slave_scratch, ap + h, bp + h);
    } else {
        toom22_12_broadwell(scratch, slave_scratch, rp, rp + h, h);       // at -1
        toom22_12_broadwell(rp, slave_scratch, ap, bp, h);                // at 0
        toom22_12_broadwell(rp + N, slave_scratch, ap + h, bp + h, h);    // at infinity
    }
    toom22_deg2_interpolate_4x(rp, scratch, sign, N);
}
#endif

// n: degree of two, 32 <= n <= 2**16
void
toom22_deg2_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n) {
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
    toom22_deg2_interpolate_4x(rp, scratch, sign, n);
}

// n: degree of two, >= 8
void
toom22_deg2_broadwell_careful(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp,
        mp_size_t n) {
    switch (n) {
    case 8:
        mul8_broadwell_store_once(rp, ap, bp);
        return;
    case 16:
        toom22_mul16_broadwell(rp, scratch, ap, bp);
        return;
    default:
        toom22_deg2_broadwell(rp, scratch, ap, bp, n);
    }
}

// N: degree of two, 32 <= N <= 2**16
template <uint16_t N>
void
toom22_deg2_broadwell_n(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    constexpr auto h = N / 2;
    constexpr auto l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto slave_scratch = scratch + N;
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    if constexpr (h < 32) {
        toom22_mul16_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_mul16_broadwell(rp, slave_scratch, ap, bp);
        toom22_mul16_broadwell(rp + N, slave_scratch, ap + h, bp + h);
    } else {
        toom22_deg2_broadwell_n<h>(scratch, slave_scratch, rp, rp + h);     // at -1
        toom22_deg2_broadwell_n<h>(rp, slave_scratch, ap, bp);              // at 0
        toom22_deg2_broadwell_n<h>(rp + N, slave_scratch, ap + h, bp + h);  // at infinity
    }
    toom22_deg2_interpolate_4x(rp, scratch, sign, N);
}

#if defined(mul6_broadwell_wr)
constexpr uint16_t TOOM_2X_BOUND = 13;

void toom22_1x_broadwell(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr, uint16_t);
void toom22_8x_broadwell(mp_ptr, mp_ptr, mp_srcptr, mp_srcptr, mp_size_t);

// n: even, not a multiple of 8, <= 2**16
void
toom22_2x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    auto h = n / 2;
    auto sign = subtract_lesser_from_bigger_1x(rp, ap, h);
    sign ^= subtract_lesser_from_bigger_1x(rp + h, bp, h);
    if (h < TOOM_2X_BOUND) {
        // __gmpn_mul_basecase: assembler subroutine from GMP
        __gmpn_mul_basecase(scratch, rp, h, rp + h, h);
        __gmpn_mul_basecase(rp, ap, h, bp, h);
        __gmpn_mul_basecase(rp + n, ap + h, h, bp + h, h);
    } else {
        auto slave_scratch = scratch + n;
        toom22_1x_broadwell(scratch, slave_scratch, rp, rp + h, h);
        toom22_1x_broadwell(rp, slave_scratch, ap, bp, h);
        toom22_1x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
    }
    // TODO: toom22_deg2_interpolate() not implemented
    //toom22_deg2_interpolate(rp, scratch, sign, n);
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

// n: not a multiple of 4, >= TOOM_2X_BOUND
void
toom22_1x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, uint16_t n) {
    if (n & 1 == 0) {
        toom22_2x_broadwell(rp, scratch, ap, bp, n);
        return;
    }
    n -= 1;
    // if below could be a speedup or a slowdown
    if (n & 7) {
        toom22_2x_broadwell(rp, scratch, ap, bp, n);
    } else {
        toom22_8x_broadwell(rp, scratch, ap, bp, n);
    }
    rp += n;
    auto tail = rp + n;
    mul_1by1(tail, ap[n], bp[n]);
    // mpn_addmul_1: asm subroutine from GMP
    auto senior = __mpn_addmul_1(rp, ap, bp[n], n);
    mpn_add_1_2arg(tail, senior);
    senior = __mpn_addmul_1(rp, bp, ap[n], n);
    mpn_add_1_2arg(tail, senior);
}

// n: multiple of 8, <= 2**16; scratch: enough for any subroutine that might be called
void
toom22_8x_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp, mp_size_t n) {
    // get rid of junior zeroes, see what is left
    uint8_t zeroes = _tzcnt_u32(n);
    auto unzeroed = n >> zeroes;
    switch (unzeroed) {
    case 1:
        toom22_deg2_broadwell_careful(rp, scratch, ap, bp, n);
        return;
    case 3:
        toom22_12_broadwell(rp, scratch, ap, bp, n);
        return;
    }
    auto h = n / 2;
    uint16_t l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto slave_scratch = scratch + n;
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    if (zeroes >= 4) {
        toom22_8x_broadwell(scratch, slave_scratch, rp, rp + h, h);         // at -1
        toom22_8x_broadwell(rp, slave_scratch, ap, bp, h);                  // at 0
        toom22_8x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);      // at infinity
    } else {
        toom22_2x_broadwell(scratch, slave_scratch, rp, rp + h, h);
        toom22_2x_broadwell(rp, slave_scratch, ap, bp, h);
        toom22_2x_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);
    }
    toom22_deg2_interpolate_4x(rp, scratch, sign, n);
}
#endif
