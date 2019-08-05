"""
shr1_10_avx2(tgt, src)

shift 10-limb src right one bit, put result into tgt

any kind of overlap allowed
"""

g_code = '''
vmovdqu (sp), w0
vperm2i128 $0x81, w0, w0, w1   | shifting w0 right 1 limb, instruction one of two
vmovdqu 24(sp), w2             |
vperm2i128 $0x81, w2, w2, w3   | shifting w2 right 1 limb, instruction one of two
vmovdqu 48(sp), w4             |
vperm2i128 $0x81, w4, w4, w5   | shifting w4 right 1 limb, instruction one of two

vpalignr $0x8, w0, w1, w1      | w1 = w0 shifted right one limb
vpalignr $0x8, w2, w3, w3      | w3 = w2 shifted right one limb
vpalignr $0x8, w4, w5, w5      | w5 = w3 shifted right one limb

vpsrlq $1, w0, w0              | w0 ~= result[0..3], 4 senior bits are wrong
vpsllq $63, w1, w1             | w1 = missing senior bits put in place
vpsrlq $1, w2, w2              | w2 ~= result[3..6], 4 senior bits are wrong
vpsllq $63, w3, w3             | w3 = missing senior bits put in place
vpsrlq $1, w4, w4              | w4 ~= result[6..9], 3 senior bits are wrong
vpsllq $63, w5, w5             | w5 = missing senior bits put in place

vpxor w1, w0, w1               | put together result[0..3], senior bit is wrong
vmovdqu w1, (rp)
vpxor w3, w2, w3               | put together result[3..6], senior bit is wrong
vmovdqu w3, 24(rp)
vpxor w5, w4, w5               | put together result[6..9]
vmovdqu w5, 48(rp)
'''

import os, sys, re
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'shr1_10_avx2',
            'input': ['rp r tgt', 'sp r src'],
            'clobber': 'memory ' + ' '.join('ymm%s' % i for i in range(6)),
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'tgt src',
            }

    all_vars = P.extract_int_vars_name(data['input'])
    code = g_code.strip() + ' '
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in range(6):
        code = re.sub(r'\bw%s\b' % i, '%%ymm' + str(i + 10), code)

    P.write_cpp_code(tgt, code.rstrip(), data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
