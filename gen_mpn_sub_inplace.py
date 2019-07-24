'''
n not a multiple of 4, n>4

mpn_sub_inplace(tgt, src, n)

subtract r := src - tgt. Place r at tgt. Put borrow (0 or 1) into n.

On exit, tgt is increased to original tgt + original n
'''

g_code = '''
movq (ap), w0
movq nn, w3
and $3, nn
shr $2, w3
subq (cp), w0
.align 32
loop_short:
lea 8(ap), ap
movq w0, (cp)
lea 8(cp), cp
dec nn
movq (ap), w0
jz done_short
sbbq (cp), w0
jmp loop_short
| m = n & 3 subtractions done, w0 = src[m]
done_short:
movq 8(ap), w1
movq w3, nn
.align 32
loop_long:
| nn = count of subtractions left / 4; 2 words of src loaded to w0 w1
lea 32(cp), cp
movq 16(ap), w2
movq 24(ap), w3            | 4 words of ap loaded
lea 32(ap), ap
sbbq -32(cp), w0
sbbq -24(cp), w1
sbbq -16(cp), w2
sbbq -8(cp), w3
movq w0, -32(cp)
movq w1, -24(cp)
dec nn
movq w2, -16(cp)
movq w3, -8(cp)
jz done_long
movq (ap), w0
movq 8(ap), w1
jmp loop_long
done_long:
adc $0, nn
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'mpn_sub_inplace',
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['nn +r n', 'cp +r tgt', 'ap +r src'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'tgt src n',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for x in 'done loop'.split(' '):
        for y in 'short long'.split(' '):
            z = x + '_' + y
            code = re.sub(r'\b%s\b' % z, z + '%=', code)

    P.write_cpp_code(tgt, code, data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
