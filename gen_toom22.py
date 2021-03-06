import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_n = int(sys.argv[1])
g_tgt = sys.argv[2]

g_code = r'''
#if TIME_INTERPOLATE
#include <x86intrin.h>

uint64_t g_time_interpolate[2];
uint64_t g_count_interpolate[2];
#endif

// scratch size: 2 * @ + what MUL_HALFSIZE needs
void
toom22_mul@_broadwell(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp) {
    static constexpr uint16_t half_n = @ / 2;
    auto sign = subtract_lesser_from_bigger_@/2(rp, ap, ap + half_n);      // a0-a1
    sign ^= subtract_lesser_from_bigger_@/2(rp + half_n, bp, bp + half_n); // b0-b1
    MUL_HALFSIZE(scratch, /* scratch? */ rp + 0, rp + half_n);             // vm1
    MUL_HALFSIZE(rp + 0, /* scratch? */ ap + 0, bp + 0);                   // v0
    MUL_HALFSIZE(rp + @, /* scratch? */ ap + half_n, bp + half_n);         // vinf
    #if TIME_INTERPOLATE
        auto t0 = __rdtsc();
    #endif
    toom22_interpolate_@(rp, scratch, sign);
    #if TIME_INTERPOLATE
        g_time_interpolate[sign] += __rdtsc() - t0;
        g_count_interpolate[sign] ++;
    #endif
}
'''.replace('@/2', '%s' % (g_n / 2)).replace('@', '%s' % g_n)

g_prefix_8 = '''
template<uint16_t, bool = true> void mul_basecase_t(mp_ptr, mp_srcptr, mp_srcptr);
'''

def do_it(tgt):
    # TODO: allow other n
    assert g_n in (8, 16)
    # don't need scratch in MUL_HALFSIZE() for n=8 or 16
    code = g_code.strip().replace(' /* scratch? */ ', ' ')
    code = re.sub('// scratch.*?\n', '', code)
    if g_n == 8:
        code = code.replace('MUL_HALFSIZE', 'mul4_broadwell_macro_wr')
    else:
        code = g_prefix_8.lstrip() + '\n' + code
        code = code.replace('MUL_HALFSIZE', 'mul_basecase_t<8>')
    tgt.write(P.g_autogenerated_patt % os.path.basename(sys.argv[0]))
    tgt.write(code + '\n')

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
