import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_n = int(sys.argv[1])
g_tgt = sys.argv[2]

def do_it(tgt):
    data = {
            'macro_name': 'mpn_le_%s' % g_n,
            'input': ['ap a_p', 'bp b_p'],
            'scratch': ['re tgt', 'w0 scratch'],
            'clobber': 'cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'vars_type': {'scratch': 'uint64_t'},
            'macro_parameters': 'tgt a_p b_p',
            }
    ofs = 8 * (g_n - 1)
    code = ['movq %s(ap), w0' % ofs, 'xorq re, re', 'subq %s(bp), w0' % ofs, 'jnz done']
    # carry flag is set iff subtraction result is negative
    
    i = g_n - 2
    while i > 0:
        ofs = 8 * i
        code += ['movq %s(ap), w0' % ofs, 'subq %s(bp), w0' % ofs, 'jnz done']
        i -= 1
    
    code += ['movq (ap), w0', 'subq (bp), w0', 'done:', 'adcq $0, re']
    
    code = '\n'.join(code)
    
    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input'])
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    code = re.sub(r'\bdone\b', 'done%=', code)
    
    P.write_cpp_code(tgt, code, data)

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
