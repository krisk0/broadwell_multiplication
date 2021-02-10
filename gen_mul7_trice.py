'''
void mul7_trice(mp_ptr rp, mp_ptr scratch, mp_srcptr ap, mp_srcptr bp);

equivalent to
{
    m7(scratch, rp, rp + 7);
    m7(rp, ap, bp);
    m7(rp + 14, ap + 7, bp + 7);
}

Calls internal function mul7_hooligan which violates Sys5 calling convention.

TODO: mul7_aligned() changed, hence mul7_trice may malfunction
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_hooligan = 'mul7_hooligan'
g_forbidden_xmm_no = set(str(i) for i in range(4, 10))
g_var_map = 'i_rp,rdi i_scratch,rsi i_ap,rdx i_bp,rcx ' + \
        's0,rbp s1,rbx s2,r12 s3,r13 s4,r14 s5,r15'

g_code = '''
sub $40, %rsp
!save s0
movq i_ap, (%rsp)          | st[0] = ap
!save s1
movq i_bp, 8(%rsp)         | st[1] = bp
!save s2
movq s4, 16(%rsp)
xchg i_rp, i_scratch       | i_scratch points to rp, i_rp points to scratch
!save s3
lea 56(i_scratch), i_ap    | i_ap points to rp + 7
movq s5, 24(%rsp)
@call                      | m7(scratch, rp, rp + 7)
movq i_scratch, i_rp       | i_rp points to rp
movq (%rsp), i_scratch     | i_scratch points to ap
movq 8(%rsp), i_ap         | i_ap points to bp
@call                      | m7(rp, ap, bp)
movq 8(%rsp), i_ap          | i_ap points to bp
lea 112(i_rp), i_rp         | i_rp points to rp + 14
lea 56(i_scratch), i_scratch | i_scratch points ap + 7
lea 56(i_ap), i_ap           | i_ap points to bp + 7
@call                        | m7(rp + 14, ap + 7, bp + 7)
!restore s3
!restore s2
movq 24(%rsp), s5
!restore s1
movq 16(%rsp), s4
!restore s0
add $40, %rsp
'''

g_xmm_pattern = re.compile(r'xmm(.+?)\b')
def chew_code(ii):
    inside,r = False,[]
    for i in ii:
        j = i.rstrip()
        if j == ' vzeroupper':
            inside = True
            continue
        if not inside:
            continue
        m = g_xmm_pattern.search(j)
        if m and m.group(1) in g_forbidden_xmm_no:
            continue
        r.append(i)
    return r

def do_it(o, i_name):
    with open(i_name, 'rb') as i:
        code = '\n'.join(chew_code(i))
    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, g_hooligan)
    P.write_asm_inside(o, code)

    code = P.cutoff_comments(g_code)
    xmm_save = P.save_registers_in_xmm(code, 5)
    P.save_in_xmm(code, xmm_save)

    code = '\n'.join(code).replace('@call', 'call ' + g_hooligan)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))
    code = P.replace_symbolic_names_wr(code, g_var_map)
    
    o.write('\n')
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[2]))
    P.write_asm_inside(o, code + '\nretq')

if __name__ == '__main__':
    with open(sys.argv[2], 'wb') as g_out:
        do_it(g_out, sys.argv[1])
