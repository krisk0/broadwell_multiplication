"""
mpn_bdiv_dbm1c_4k_inplace(r_p, n, m)

exactly divide n-limb number at r_p by k, store result in-place. n is multiple of four.
 m_m * k == -1 (mod 2**64)
"""

g_code = '''
xor w2,w2                        | w2 = 0
mulx (rp), w0, w1
lea (rp,nn,8), rp                | rp now one limb past tail of the number
neg nn
jmp enter_here

.align 16
loop:
mulx (rp,nn,8), w0, w1
enter_here:
sub w0, w2
mov w2, w3                       | w3 must be stored at (rp,nn,8)
sbb w1, w2

mulx 8(rp,nn,8), w0, w1
sub w0, w2
mov w3, (rp,nn,8)
mov w2, 8(rp,nn,8)
sbb w1, w2

mulx 16(rp,nn,8), w0, w1
sub w0, w2
mov w2, w3                       | w3 must be stored at 16(rp,nn,8)
sbb w1, w2

mulx 24(rp,nn,8), w0, w1
sub w0, w2
mov w3, 16(rp,nn,8)
mov w2, 24(rp,nn,8)
sbb w1, w2

add $4, nn
jnz loop
'''

g_wr_code = '''
#define mpn_bdiv_dbm1c_4k_inplace_wr(r, n, m)
    {
        mp_ptr bdiv_dbm1c_4k_inplace_r = r;
        mp_limb_t bdiv_dbm1c_4k_inplace_n = n;
        mp_limb_t bdiv_dbm1c_4k_inplace_m = m;
        mpn_bdiv_dbm1c_4k_inplace(bdiv_dbm1c_4k_inplace_r, bdiv_dbm1c_4k_inplace_n,
                bdiv_dbm1c_4k_inplace_m);
'''

g_func_code = '''
void
__attribute__ ((noinline))
mpn_bdiv_dbm1c_4k_inplace_func(mp_ptr r_p, mp_limb_t n, mp_limb_t m) {
    mpn_bdiv_dbm1c_4k_inplace(r_p, n, m);
}
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'mpn_bdiv_dbm1c_4k_inplace',
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['rp +r r_p', 'mm +d m', 'nn +r n'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p n m',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in 'loop enter_here'.split(' '):
        code = re.sub(r'\b%s\b' % i, i + '%=', code + ' ').rstrip()

    P.write_cpp_code(tgt, code, data)
    tgt.write('\n')
    for i in g_wr_code.strip().split('\n'):
        tgt.write(P.append_backslash(i, 88))
    tgt.write('    }\n')
    tgt.write(g_func_code)

g_tgt = sys.argv[1]

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
