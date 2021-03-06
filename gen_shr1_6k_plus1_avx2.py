"""
shr1_6k_plus1_avx2(adr, k)

shift 6k+1-limb number right one bit in-place. k>=1, any number type.

On Haswell 54 ticks for k=61
"""

g_code = '''
vmovdqu (rp), w0
vperm2i128 $0x81, w0, w0, w1   | shifting w0 right 1 limb, instruction one of two
vmovdqu 24(rp), w2             |
vperm2i128 $0x81, w2, w2, w3   | shifting w2 right 1 limb, instruction one of two

.align 32
loop:

vpalignr $0x8, w0, w1, w1      | w1 = w0 shifted right one limb
vpalignr $0x8, w2, w3, w3      | w3 = w2 shifted right one limb

vpsrlq $1, w0, w0              | w0 ~= result[0..3], 4 senior bits are wrong
vpsllq $63, w1, w1             | w1 = missing senior bits put in place
vpsrlq $1, w2, w2              | w2 ~= result[3..6], 4 senior bits are wrong
vpsllq $63, w3, w3             | w3 = missing senior bits put in place

sub $1, kk                     | TODO: dec should be used instead?
jz nearly_done

vpxor w1, w0, w1               | put together result[0..3], senior bit is wrong
vmovdqu w1, (rp)
vmovdqu 48(rp), w0
vperm2i128 $0x81, w0, w0, w1   | shifting w0 right 1 limb, instruction one of two

vpxor w3, w2, w3               | put together result[3..6], senior bit is wrong
vmovdqu w3, 24(rp)
vmovdqu 72(rp), w2             |
vperm2i128 $0x81, w2, w2, w3   | shifting w2 right 1 limb, instruction one of two

lea 48(rp), rp
jmp loop

nearly_done:
vpxor w1, w0, w1               | put together result[0..3], senior bit is wrong
vmovdqu w1, (rp)
vpxor w3, w2, w3               | put together result[3..6]
vmovdqu w3, 24(rp)
'''

import os, sys, re
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'shr1_6k_plus1_avx2',
            'input_output': ['rp +r adr', 'kk +r k'],
            'clobber': 'memory cc ' + ' '.join('ymm%s' % i for i in range(4)),
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'adr k',
            }

    all_vars = P.extract_int_vars_name(data['input_output'])
    code = g_code.strip() + ' '
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in range(4):
        code = re.sub(r'\bw%s\b' % i, '%%ymm' + str(i + 12), code)
    for i in 'loop nearly_done'.split(' '):
        code = re.sub(r'\b%s\b' % i, i + '%=', code)

    P.write_cpp_code(tgt, code.rstrip(), data)

with open(sys.argv[1], 'wb') as g_o:
    do_it(g_o)
