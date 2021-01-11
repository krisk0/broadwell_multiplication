'''
subtract from 7-limb number a 6-limb number b.

a is at a_p. b is at a_p + 56
'''

g_code = '''
movq 0(ap), w0
movq 1(ap), w1
movq 2(ap), w2
movq 3(ap), w3
subq 0(bp), w0
sbbq 1(bp), w1
sbbq 2(bp), w2
sbbq 3(bp), w3
movq w0, 0(rp)
movq w1, 1(rp)
movq w2, 2(rp)
movq w3, 3(rp)
movq 4(ap), w0
movq 5(ap), w1
movq 6(ap), w2
sbbq 4(bp), w0
sbbq 5(bp), w1
sbbq $0, w2
movq w0, 4(rp)
movq w1, 5(rp)
movq w2, 6(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_b_patt = re.compile(r'(.)\(bp\)')
g_a_patt = re.compile(r'(.)\((.p)\)')
def chew_line(s, b_ofs):
    m = g_b_patt.search(s)
    if m:
        return s.replace(m.group(), '%s(ap)' % (b_ofs * 8 + int(m.group(1)) * 8))

    m = g_a_patt.search(s)
    if m:
        return s.replace(m.group(), '%s(%s)' % (int(m.group(1)) * 8, m.group(2)))

    return s

def do_it(tgt, code, b_ofs):
    data = {
            'macro_name': P.guess_subroutine_name(sys.argv[1]),
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input': ['rp r r_p', 'ap r a_p'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p a_p',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + ['ap', 'rp']
    code = '\n'.join([chew_line(x, b_ofs) for x in P.cutoff_comments(code)])
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    P.write_cpp_code(tgt, code, data)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        do_it(g_o, g_code, 7)
