'''
n not a multiple of 4, n>4, a >= b

mpn_sub_1x(r_p, a_p, b_p, n)

r := a - b

modify all 4 arguments

TODO: 64-bit dec is slower than 16-bit dec? If yes then must arrange it so that counter
 is 16 bit
'''

g_code = '''
movq (ap), w0
movq nn, kk
add $3, nn
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
movq w0, (rp)
movq w1, 8(rp)
dec kk
movq w2, 16(rp)
movq w3, 24(rp)
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
    code = re.sub(r'\bw3\b', 'nn', code)

    data = {
            'macro_name': 'mpn_sub_1x',
            'scratch': ['w%s s%s' % (i, i) for i in range(3)] + ['kk s3'],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['nn +r n', 'rp +r r_p', 'ap +r a_p', 'bp +r b_p'],
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

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)