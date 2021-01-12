'''
void mpn_add_4k_plus2_4arg(mp_ptr t_p, mp_limb_t u_s, mp_srcptr u_p, uint16_t loops);

add n+1-word number u_s u_p[n-1] u_p[n-2] ... u_p[1] u_p[0] to t (of bigger length)
when propagating carry, don't worry that is goes too far

n = 4 * loops + 2
'''

g_code = '''
movq (tp), w0
movq 8(tp), w1     | (w1) (w0)
xor w2, w2
.align 32
main_loop:
adcq (up), w0
adcq 8(up), w1
movq 16(tp), w2
movq 24(tp), w3    | (w3) (w2) w1 w0
movq w0, (tp)
movq w1, 8(tp)     | (w3) (w2)
lea 32(tp), tp
adcq 16(up), w2
adcq 24(up), w3    | w3 w2
movq (tp), w0
movq 8(tp), w1     | (w1) (w0) w3 w2
movq w2, -16(tp)
movq w3, -8(tp)    | (w1) (w0)
dec lc
lea 32(up), up
jne main_loop
adcq (up), w0
adcq 8(up), w1     | w1 w0
movq w0, (tp)
movq w1, 8(tp)
adcq us, 16(tp)
.align 32
carry_loop:
lea 8(tp), tp
adcq $0, 16(tp)
jc carry_loop
'''

g_var_map = 'tp,rdi us,rsi up,rdx lc,cx w0,rax w1,r8 w2,r9 w3,r10'

import os, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(o, code, var_map):
    code = '\n'.join(P.cutoff_comments(code))
    code = P.replace_symbolic_names_wr(code, var_map)
    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out, g_code, g_var_map)