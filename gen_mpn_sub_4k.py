"""
mpn_sub_4k(r_p, a_p, b_p, loop_count)

a, b -- numbers of equal word-length: loop_count * 4 + 4

subtract b from a, put result at r_p: r := a - b

loop_count is of any basic unsigned integer type (uintX_t)
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq (ap), w0
movq 8(ap), w1
movq 16(ap), w2
movq 24(ap), w3
lea 32(ap), ap
subq (bp), w0
sbbq 8(bp), w1                       | (w3) (w2) w1 w0
.align 32
loop:
sbbq 16(bp), w2
sbbq 24(bp), w3
lea 32(bp), bp
movq w0, (rp)
movq w1, 8(rp)                       | w3 w2
movq (ap), w0
movq 8(ap), w1                       | (w1) (w0) w3 w2
lea 32(ap), ap
movq w2, 16(rp)
movq w3, 24(rp)                      | (w1) (w0)
movq -16(ap), w2
movq -8(ap), w3                      | (w3) (w2) (w1) (w0)
sbbq (bp), w0
sbbq 8(bp), w1                       | (w3) (w2) w1 w0
dec lc
lea 32(rp), rp
jne loop
sbbq 16(bp), w2
sbbq 24(bp), w3                      | w3 w2 w1 w0
movq w0, (rp)
movq w1, 8(rp)
movq w2, 16(rp)
movq w3, 24(rp)
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_sub_4k',
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['rp +r r_p', 'ap +r a_p', 'bp +r b_p', 'lc +r loop_count'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p a_p b_p loop_count',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    code = re.sub(r'\bloop\b', 'loop%=', code)

    P.write_cpp_code(tgt, code, data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
