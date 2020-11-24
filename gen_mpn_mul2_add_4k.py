"""
mpn_mul2_add_4k(r_p, u_p, v_p, k)

Input: 4*k-limb numbers u and v, k >= 1, k of type uint64_t
Compute r := 2*u + v. Put 4k+1-limb number r onto r_p
"""

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_code = '''
movq (up), w0
movq 8(up), w1
xorq w3, w3            | TODO: move this line
movq 16(up), w2
movq 24(up), w3        | (w3) (w2) (w1) (w0)
adcx (up), w0
adcx 8(up), w1         | (w3) (w2) [w1] [w0]
.align 32

loop:
lea -1(lc), lc
adcx 16(up), w2
adcx 24(up), w3        | [w3] [w2] [w1] [w0]
jrcxz nearly_done
lea 32(up), up
adox (vp), w0
adox 8(vp), w1
adox 16(vp), w2
adox 24(vp), w3        | w3 w2 w1 w0
movq w0, (rp)
movq w1, 8(rp)         | w3 w2
lea 32(vp), vp
movq (up), w0
movq 8(up), w1         | w3 w2 (w1) (w0)
movq w2, 16(rp)
movq w3, 24(rp)        | (w1) (w0)
movq 16(up), w2
movq 24(up), w3        | (w3) (w2) (w1) (w0)
adcx (up), w0
adcx 8(up), w1         | (w3) (w2) [w1] [w0]
lea 32(rp), rp
jmp loop

nearly_done:           | [w3] [w2] [w1] [w0]
adcx lc, lc
adox (vp), w0
adox 8(vp), w1
adox 16(vp), w2
adox 24(vp), w3        | w3 w2 w1 w0
movq w0, (rp)
movq w1, 8(rp)
movq $0, w0
movq w2, 16(rp)
movq w3, 24(rp)
adox w0, lc
movq lc, 32(rp)
'''

g_wr_code = '''
#define mpn_mul2_add_4k_wr(r, u, v, k)
    {
        auto mpn_mul2_add_4k_wr_r = r;
        auto mpn_mul2_add_4k_wr_u = u;
        auto mpn_mul2_add_4k_wr_v = v;
        uint64_t mpn_mul2_add_4k_wr_k = k;
        mpn_mul2_add_4k(mpn_mul2_add_4k_wr_r, mpn_mul2_add_4k_wr_u,
                mpn_mul2_add_4k_wr_v, mpn_mul2_add_4k_wr_k);
'''

def do_it(tgt):
    data = {
            'macro_name': 'mpn_mul2_add_4k',
            'scratch': ['w%s s%s' % (i, i) for i in range(4)],
            'vars_type': dict([('s%s' %i, 0) for i in range(4)]),
            'default_type': 'mp_limb_t',
            'input_output': ['rp +r r_p', 'up +r u_p', 'vp +r v_p', 'lc +c k'],
            'clobber': 'memory cc',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p u_p v_p k',
            }

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input_output'])
    code = g_code.strip()
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    for l in 'loop nearly_done'.split(' '):
        code = re.sub(r'\b%s\b' % l, l + '%=', code)

    P.write_cpp_code(tgt, code, data)
    
    # append wrapper code
    tgt.write('\n')
    for i in g_wr_code.strip().split('\n'):
        tgt.write(P.append_backslash(i, 77))
    tgt.write('    }\n')

g_tgt = sys.argv[1]

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
