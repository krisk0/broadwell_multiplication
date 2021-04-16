'''
n not a multiple of 4, n>4, a >= b

mpn_sub_1x(r_p, a_p, b_p, n)

n should be a 16-bit var

r := a - b

modify all 4 arguments
'''

g_code = '''
movq (ap), w0
mov nn, kk
and $3, nn
shr $2, kk
subq (bp), w0
.align 32
loop_short:
lea 8(bp), bp
movq w0, (rp)
lea 8(rp), rp
dec nn
movq 8(ap), w0
lea 8(ap), ap
jz done_short
sbbq (bp), w0
jmp loop_short
done_short:
| m = n & 3 subtractions done, w0 = a[m], all 3 pointers grew by m, kk = n//4
movq 8(ap), w1
.align 32
loop_long:
| kk = count of subtractions left / 4; 2 words of src loaded to w0 w1
lea 32(rp), rp
movq 16(ap), w2
movq 24(ap), w3            | 4 words of ap loaded
lea 32(ap), ap             | rp, ap grew
sbbq (bp), w0
sbbq 8(bp), w1
sbbq 16(bp), w2
sbbq 24(bp), w3
lea 32(bp), bp             | all 3 pointers grew
movq w0, -32(rp)
movq w1, -24(rp)
dec kk
movq w2, -16(rp)
movq w3, -8(rp)
jz done_long
movq (ap), w0
movq 8(ap), w1
jmp loop_long
done_long:
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    code = g_code.strip()
    code = re.sub(r'\bw3\b', '%%rax', code)
    scr = dict([('s%s' %i, 0) for i in range(3)])
    scr['s3'] = 'uint16_t'

    data = {
            'macro_name': 'mpn_sub_1x',
            'scratch': ['w%s s%s' % (i, i) for i in range(3)] + ['kk s3'],
            'vars_type': scr,
            'default_type': 'mp_limb_t',
            'input_output': ['nn +a n', 'rp +r r_p', 'ap +r a_p', 'bp +r b_p'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p a_p b_p n',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])

    for x in 'done loop'.split(' '):
        for y in 'short long'.split(' '):
            z = x + '_' + y
            code = re.sub(r'\b%s\b' % z, z + '%=', code)

    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    P.write_cpp_code(tgt, code, data)

with open(sys.argv[1], 'wb') as g_o:
    do_it(g_o)
