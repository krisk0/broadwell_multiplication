"""
shr1_4_avx2(tgt, src)

shift 4-limb src right one bit, put result into tgt

any kind of overlap allowed
"""

g_code = '''
vmovdqu (sp), w0

vperm2i128 $0x81, w0, w0, w1   | sequence of 2 spells vperm2i128 vpalignr
vpalignr $0x8, w0, w1, w1      | w1 = w0 shifted right one limb

vpsrlq $1, w0, w0              | w0 nearly = result, 4 senior bits are all zero
vpsllq $63, w1, w1             | w1 = missing senior bits put in place
vpxor w1, w0, w0

vmovdqu w0, (rp)
'''

import os, sys, re
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'shr1_4_avx2',
            'input': ['rp r tgt', 'sp r src'],
            'clobber': 'memory ' + ' '.join('ymm%s' % i for i in range(2)),
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'tgt src',
            }

    all_vars = P.extract_int_vars_name(data['input'])
    code = g_code.strip() + ' '
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for i in range(2):
        code = re.sub(r'\bw%s\b' % i, '%%ymm' + str(i + 14), code)

    P.write_cpp_code(tgt, code.rstrip(), data)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
