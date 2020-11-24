"""
mpn_less_3arg_hole(result, v_head, v_tail)

u, v -- numbers of equal limb-length, u ends at v_head-16, v is at v_head..v_tail-8

set result to 1 if number u is less than number v, 0 otherwise

result is of any basic integer type
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq -16(up), w2                   | w2 := senior limb of u
xor rr, rr                         | size unset, defined by rr size (8, 16, 32 or 64 bits)
lea -8(up), w0                     | copy of up that will decrease
movq vp, w1                        | copy of vp that will decrease
.align 32
loop:
lea -8(w0), w0                     | move pointer w0
subq -8(w1), w2                    | w1 := w2 - v[x]
lea -8(w1), w1                     | move pointer w1, w1 = address of last checked v
jne done                           | if not equal, all done
cmp up, w1                         | was that v[0]?
je done                            | last checked v was v[0], can't go any further
movq -8(w0), w2                    | w2 := next limb of u
jmp loop
done:
adc $0, rr                         | size unset, defined by rr size
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_less_3arg_hole',
            'scratch': ['rr result'] + ['w%s s%s' % (i, i) for i in range(3)],
            'vars_type': dict([('s%s' %i, 0) for i in range(3)]),
            'default_type': 'mp_limb_t',
            'input': ['up v_head', 'vp v_tail'],
            'clobber': 'cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'result v_head v_tail',
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

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
