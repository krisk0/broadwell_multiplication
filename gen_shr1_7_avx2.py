"""
shr1_7_avx2(tgt, src)

shift 7-limb src right one bit, put result into tgt

any kind of overlap allowed
"""

g_code = '''
vmovdqu (sp), w0
vperm2i128 $0x81, w0, w0, w1   | shifting w0 right 1 limb, instruction one of two
vmovdqu 24(sp), w2             | in-between load remaining data into w2
vperm2i128 $0x81, w2, w2, w3   | shifting w2 right 1 limb, instruction one of two
vpalignr $0x8, w0, w1, w1      | w1 = w0 shifted right one limb
vpalignr $0x8, w2, w3, w3      | w3 = w2 shifted right one limb
vpsrlq $1, w0, w0              | w0 ~= result junior 4 limbs, 4 senior bits are wrong
vpsllq $63, w1, w1             | w1 = missing senior bits put in place
vpsrlq $1, w2, w2              | w2 ~= result[3..6], 3 senior bits are wrong
vpsllq $63, w3, w3             | w3 = missing senior bits put in place
vpxor w1, w0, w1               | put together 1st part of result, senior bit is wrong
vmovdqu w1, (rp)
vpxor w3, w2, w3               | put together 2nd part of result
vmovdqu w3, 24(rp)
'''

import os, sys, re
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'shr1_7_avx2',
            'input': ['rp r tgt', 'sp r src'],
            'clobber': 'memory ' + ' '.join('ymm%s' % i for i in range(4)),
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'tgt src',
            }

    all_vars = P.extract_int_vars_name(data['input'])
    code = g_code.strip() + ' '
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in range(4):
        code = re.sub(r'\bw%s\b' % i, '%%ymm' + str(i + 12), code)

    P.write_cpp_code(tgt, code.rstrip(), data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
