"""
mpn_add_4k_inplace(carry, c_p, a_p, loop_count)

loop_count > 0

c, a -- numbers of equal word-length loop_count * 4 + 4 .

Add a to c in place, put result onto c. Modify c_p, a_p, loop_count. Add carry to carry.

loop_count is of any basic unsigned integer type (uintX_t)
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq (cp), w0
movq 8(cp), w1
movq 16(cp), w2
movq 24(cp), w3                      | (w3) (w2) (w1) (w0)
lea 32(cp), cp
addq (ap), w0
adcq 8(ap), w1                       | (w3) (w2) w1 w0
.align 32
loop:
adcq 16(ap), w2
adcq 24(ap), w3                      | w3 w2 w1 w0
lea 32(ap), ap
movq w0, -32(cp)
movq w1, -24(cp)                     | w3 w2
movq (cp), w0
movq 8(cp), w1                       | (w1) (w0) w3 w2
movq w2, -16(cp)
movq w3, -8(cp)                      | (w1) (w0)
movq 16(cp), w2
movq 24(cp), w3                      | (w3) (w2) (w1) (w0)
adcq (ap), w0
adcq 8(ap), w1                       | (w3) (w2) w1 w0
dec lc
lea 32(cp), cp
jne loop
adcq 16(ap), w2
adcq 24(ap), w3                      | w3 w2 w1 w0
movq w0, -32(cp)
movq w1, -24(cp)
adcq $0, ca
movq w2, -16(cp)
movq w3, -8(cp)
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_add_4k_inplace',
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

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
