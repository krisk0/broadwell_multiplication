#include <immintrin.h>

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

// memory layout: a+0 a+1 ... a+n-1 b+0 b+1 ... a+n-1
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
subtract_in_place_then_add(mp_ptr tgt, mp_srcptr ab_p, mp_size_t n, uint16_t l) {
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

/*
n := 2*loops + 1
add n+1-word number t_s t_p[n-1] t_p[n-2] ... t_p[1] t_p[0] to y (of bigger length)
when propagating carry, don't worry that is goes too far
*/
void
mpn_add_n_plus_1(mp_ptr y_p, mp_limb_t t_s, mp_srcptr t_p, uint16_t loops) {
    auto n = 4 * (loops + 1);
    auto carry_p = y_p + n;
    #if 0
        printf("loops=%d  n=%ld\n", loops, n);
        printf("carry adr: " PRINTF_FORMAT "  y_p adr:" PRINTF_FORMAT "\n", carry_p,
                y_p);
        printf("mpn_add_n_plus_1() input carry: " PRINTF_FORMAT "\n", t_s);
        auto y_p_saved = y_p;
        printf("y before adding:\n"); dump_number(y_p_saved, 64 - 16);
    #endif
    mpn_add_4k_inplace(t_s, y_p, t_p, loops);
    #if 0
        printf("mpn_add_n_plus_1() modified carry: " PRINTF_FORMAT "\n", t_s);
        printf("y after adding:\n"); dump_number(y_p_saved, 64 - 16);
        printf("carry adr: " PRINTF_FORMAT "  y_p adr:" PRINTF_FORMAT "\n", carry_p,
                y_p_saved);
    #endif
    mpn_add_1_2arg(carry_p, t_s);
    #if 0
        printf("y after carry:\n"); dump_number(y_p_saved, 64 - 16);
    #endif
}

/*
memory layout:
               <--       b      ->  <-     a     ->
               b(n-1) ... b(1) b(0) a(n-1) ... a(0)
                                                 ^
                                                 |
                                                ap

g := n-word number at g_p

subroutine operation:
t := -(-1)**sign * g + a + b, t bit-length is not more than n*64 + 2
add number t to number y := b(n-1) ... b(1) a(n-1) ... a(n/2+1) a(n/2)
replace y with result of the addition

carry cannot get past senior end of number y when adding t, so it is unnecessary to check
 index range when propagating carry
*/
void
toom22_deg2_interpolate(mp_ptr ab_p, mp_ptr g_p, uint8_t sign, mp_size_t n) {
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
        t_senior = subtract_in_place_then_add(g_p, ab_p, n, l);
    }
    mpn_add_n_plus_1(ab_p + (n / 2), t_senior, g_p, l);
}

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
    if (h >= 32) {
        toom22_deg2_broadwell(scratch, slave_scratch, rp, rp + h, h);       // vm1
        toom22_deg2_broadwell(rp, slave_scratch, ap, bp, h);                // v0
        toom22_deg2_broadwell(rp + n, slave_scratch, ap + h, bp + h, h);    // vinf
    } else {
        toom22_mul16_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_mul16_broadwell(rp, slave_scratch, ap, bp);
        toom22_mul16_broadwell(rp + n, slave_scratch, ap + h, bp + h);
    }
    toom22_deg2_interpolate(rp, scratch, sign, n);
}

// n: degree of two, 32 <= n <= 2**16
template <uint16_t N>
void
toom22_deg2_broadwell_n(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    constexpr auto h = N / 2;
    auto l = (h >> 2) - 1;                // count of loops inside mpn_sub_4k()
    auto slave_scratch = scratch + N;
    auto sign = subtract_lesser_from_bigger_n(rp, ap, h, l);                // a0-a1
    sign ^= subtract_lesser_from_bigger_n(rp + h, bp, h, l);                // b0-b1
    if constexpr (h >= 32) {
        toom22_deg2_broadwell_n<h>(scratch, slave_scratch, rp, rp + h);       // vm1
        toom22_deg2_broadwell_n<h>(rp, slave_scratch, ap, bp);                // v0
        toom22_deg2_broadwell_n<h>(rp + N, slave_scratch, ap + h, bp + h);    // vinf
    } else {
        toom22_mul16_broadwell(scratch, slave_scratch, rp, rp + h);
        toom22_mul16_broadwell(rp, slave_scratch, ap, bp);
        toom22_mul16_broadwell(rp + N, slave_scratch, ap + h, bp + h);
    }
    toom22_deg2_interpolate(rp, scratch, sign, N);
}
