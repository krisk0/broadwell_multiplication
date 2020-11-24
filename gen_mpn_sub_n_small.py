"""
mpn_sub_n_small(rp, ap, bp, n)

n in range 1..3 -- size of numbers

subtract b from a, put result into rp: r := a - b

if no carry occurs, set n to zero. Else set n to 1

rp, ap, bp destroyed
"""

g_code = '''
movq (ap), w0
lea 8(ap), ap
subq (bp), w0
.align 32
loop:
movq w0, (rp)
dec lc
lea 8(rp), rp
jz done
movq (ap), w0
lea 8(ap), ap
sbbq 8(bp), w0
lea 8(bp), bp
jmp loop
done:
adc $0, lc
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'mpn_sub_n_small',
            'scratch': ['w0 s0'],
            'vars_type': {'s0': 0},
            'default_type': 'mp_limb_t',
            'input_output': ['rp +r r_p', 'ap +r a_p', 'bp +r b_p', 'lc +r n'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p a_p b_p n',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in 'loop', 'done':
        code = re.sub(r'\b%s\b' % i, i + '%=', code)

    P.write_cpp_code(tgt, code, data)

with open(sys.argv[1], 'wb') as g_o:
    do_it(g_o)
