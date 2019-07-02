"""
mpn_less_3arg(result, a_tail, b_tail)

a, b -- numbers of equal word-length, a ends at a_tail-8, b is at a_tail..b_tail-8

set result to 1 if number a is less than number b, 0 otherwise

result is of any basic integer type

destroy a_tail and b_tail
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq -8(ap), w2
xor rr, rr                         | size unset, defined by rr size (8, 16, 32 or 64 bits)
movq ap, w0
movq bp, w1
.align 32
loop:
lea -8(w0), w0
subq -8(w1), w2
lea -8(w1), w1
jne done
cmp ap, w1
je done                            | a=b, carry is zero
movq -8(w0), w2
jmp loop
done:
adc $0, rr                         | size unset, defined by rr size
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_less_3arg',
            'scratch': ['rr result'] + ['w%s s%s' % (i, i) for i in range(3)],
            'vars_type': dict([('s%s' %i, 0) for i in range(3)]),
            'default_type': 'mp_limb_t',
            'input': ['ap a_tail', 'bp b_tail'],
            'clobber': 'cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'result a_tail b_tail',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for x in 'done loop'.split(' '):
        code = re.sub(r'\b%s\b' % x, x + '%=', code)
    
    P.write_cpp_code(tgt, code, data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
