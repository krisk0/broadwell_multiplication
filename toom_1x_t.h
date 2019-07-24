#if 0
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

template <uint16_t h, uint16_t q>
uint8_t
subtract_lesser_from_bigger(mp_ptr tgt, mp_srcptr a_p) {
    if (a_p[q]) {
        auto borrow = mpn_sub(tgt, a_p, a_p + h, q);
        tgt[q] = a_p[q] - borrow;
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
    mpn_less_3arg_hole(less, u_tail, w_tail);
    if (less) {
        mpn_sub(tgt, u_tail + 1, a_p, q);
    } else {
        mpn_sub(tgt, a_p, u_tail + 1, q);
    }
    tgt[q] = 0;
    return less;
}

template <uint16_t h, uint16_t q>
uint8_t
v1(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    // place one subtraction result at scratch + 2*h
    auto sign = subtract_lesser_from_bigger<h, q>(scratch + 2*h, ap);
    // place another subtraction result at rp
    sign ^= subtract_lesser_from_bigger<h, q>(rp, bp);
    toom22_broadwell_t<h>(scratch, scratch + 3*h, scratch + 2*h, rp);
    return sign;
}

/*
|v1| of size 2*h at scratch + 0
v0 of size 2*h at rp + 0
v2 of size 2*q at rp + 2 * h

do Toom22 interpolation:
v3 = v2 + v0 - v1           2*h limbs
add 2*h-limb v3 to number at rp + h

v3 is known to fit 2*h limbs, which means that limb at index 2*h need not be cared
 for. For instance, no carry from limb at index 2*h-1 is possible when calculating
 v3 = v2 + v0 + |v1|.
*/


template <uint16_t h, uint16_t q>
void
interpolate(mp_ptr rp, mp_ptr scratch, uint8_t v1_sign) {
    if (v1_sign) {
        // v3 = v2 + v0 + |v1|
        (void)mpn_add_n(scratch, scratch, rp, 2 * h);
        // v2 is 2 limbs shorter, need to spread carry
        auto carry = mpn_add_n(scratch, scratch, rp + 2 * h, 2 * q);
        mpn_add_1_2arg(scratch + 2 * q, carry);
    } else {
        // v3 = v0 - |v1| + v0
    }
}

} // end namespace toom22_1x

// N: odd, >= TOOM_2X_BOUND
template <uint16_t N>
void
toom22_1x_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    constexpr auto h = (N + 1) / 2;
    constexpr auto q = h - 1;
    auto v1_sign = toom22_1x::v1<h, q>(rp, scratch, ap, bp);   // |v1| now at scratch + 0
    toom22_broadwell_t<h>(rp, scratch + 2 * h, ap, bp);        // v0 at rp + 0
    toom22_broadwell_t<q>(rp + 2 * h, scratch + 2 * h, ap + h, bp + h); // v2 at rp + 2*h
    toom22_1x::interpolate<h, q>(rp, scratch, sign);
}

// N: integer, not very big
template <uint16_t N>
void
toom22_broadwell_t(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    if constexpr (N < TOOM_2X_BOUND) {
        // use a fast subroutine if possible
        if constexpr (N == 8) {
            mul8_broadwell_store_once(rp, ap, bp);
            return;
        }
        if constexpr (N == 6) {
            mul6_broadwell(rp, ap, bp);
            return;
        }
        // call asm subroutine from GMP, bypassing if's in mpn_mul_n()
        __gmpn_mul_basecase(rp, ap, N, bp, N);
   } else {
        if constexpr (N & 1) {
            toom22_1x_broadwell_t<N>(rp, scratch, ap, bp);
        } else {
            toom22_2x_broadwell_t<N>(rp, scratch, ap, bp);
        }
    }
}
