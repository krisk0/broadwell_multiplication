"""
mpn_sub_4k_inplace(carry, c_p, a_p, loop_count)

loop_count > 0

n := loop_count * 4 + 4
m := 2**(2 + 64*n)

c, a -- numbers of equal word-length n .

This macro subtracts c from a modulo m, puts result into carry and c_p:

t := a - c mod m
carry += t(n)
put t(n-1) t(n-2) ... t(0) onto c_p

On exit, c_p, a_p and loop_count are destroyed

loop_count is of any basic unsigned integer type (uintX_t)
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq (ap), w0
movq 8(ap), w1
movq 16(ap), w2
movq 24(ap), w3                       | (w3) (w2) (w1) (w0)
subq (cp), w0
sbbq 8(cp), w1                        | (w3) (w2) w1 w0
.align 32
loop:
lea 32(ap), ap
sbbq 16(cp), w2
sbbq 24(cp), w3                       | w3 w2 w1 w0
movq w0, (cp)
movq w1, 8(cp)                        | w3 w2
movq (ap), w0
movq 8(ap), w1                        | (w1) (w0) w3 w2
movq w2, 16(cp)
movq w3, 24(cp)                       | (w1) (w0)
lea 32(cp), cp
movq 16(ap), w2
movq 24(ap), w3                       | (w3) (w2) (w1) (w0)
sbbq (cp), w0
sbbq 8(cp), w1                        | (w3) (w2) w1 w0
dec lc
jne loop
sbbq 16(cp), w2
sbbq 24(cp), w3                       | w3 w2 w1 w0
movq w0, (cp)
movq w1, 8(cp)                        | w3 w2
adc $0, ca
movq w2, 16(cp)
movq w3, 24(cp)                        | w3 w2
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_sub_4k_inplace',
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['ca +r carry', 'cp +r c_p', 'ap +r a_p', 'lc +r loop_count'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'carry c_p a_p loop_count',
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
