'''
6x6 multiplication targeting Ryzen, uses red zone.
'''

g_var_map = 'wD,rdi wC,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx ' + \
    'rp,xmm15 t0,xmm14 t1,xmm13 t2,xmm12'

"""
Red zone layout:
sp-128 sp-120 sp-112 sp-104 sp-96 .. sp-16 sp-8
  u2     u3     u4      u5    R0  ..  R10   R11
"""

g_preamble = '''
vzeroupper
movq dd, w0
!save w6
movq (wC), w6
!save w7
movq 8(wC), w7
!save w8
movq 16(wC), w8
!save w9
movq 24(wC), w9
!save wA
movq 32(wC), wA
!save wB
movq 40(wC), wB       | w[x+6]=u[x]
movq wD, rp           | rp = pointer to target
movq (w0), dd         | dd=v[0]
movq 8(w0), t0        | t0=v[1]
movq 16(w0), w1       | w1=v[2]
mulx w6, w3, w2       | w2 w3
mulx w7, w5, wC       | wC w2+w5 w3
movq 24(w0), t1       | t1=v[3]
movq 32(w0), w4       | w4=v[4]
movq 40(w0), t2       | t2=v[5]
pinsrq $1, w1, t0     | t0=v[1..2]
mulx w8, w0, w1       | w1 wC+w0 w2+w5 w3
pinsrq $1, w4, t1     | t1=v[3..4]
movq wA, @u[4]
movq wB, @u[5]
mulx w9, wA, w4       | w4 w1+wA wC+w0 w2+w5 w3
movq w3, @r[0]        | w4 w1+wA wC+w0 w2+w5 ..
mulx @u[4], w3, wB    | wB w4+w3 w1+wA wC+w0 w2+w5 ..
addq w5, w2           | wB w4+w3 w1+wA wC+w0' w2 ..
w5:=v[1]
movq w2, @r[1]        | wB w4+w3 w1+wA wC+w0' [2] w5=v[1]
mulx @u[5], w2, wD    | wD wB+w2 w4+w3 w1+wA wC+w0' [2] w5=v[1]
adcq wC, w0           | wD wB+w2 w4+w3 w1+wA' w0 [2] w5=v[1]
adcq wA, w1           | wD wB+w2 w4+w3' w1 w0 [2] w5=v[1]
adcq w3, w4           | wD wB+w2' w4 w1 w0 [2] w5=v[1]
adcq wB, w2           | wD' w2 w4 w1 w0 [2] w5=v[1]
xchg dd, w5           | wD' w2 w4 w1 w0 [2]
'''

"""
i>=1
multiplied by v[0..i-1]
data lies like that: | sD; s2 s4 s1 s0 [i+1] dd=v[i]
                                                     s6=u[0] s7=u[1] s8=u[2] s9=u[3]
"""

g_mul_1 = '''
                     | sD; s2 s4 s1 s0 .. [i]
mulx s6, s5, sA      | sD; s2 s4 s1 s0+sA s5| [i]
mulx s7, sB, sC      | sD; s2 s4 s1+sC s0+sA+sB s5| [i]
adcq $0, sD          | sD s2 s4 s1+sC s0+sA+sB s5| [i]
movq s1, @r[i+2]     | sD s2 s4 sC| s0+sA+sB s5| [i]
mulx s8, s1, s3      | sD s2 s4+s3 sC+s1| s0+sA+sB s5| [i]
movq s4, @r[i+3]     | sD s2 s3| sC+s1| s0+sA+sB s5| [i]
movq s2, @r[i+4]     | sD .. s3| sC+s1| s0+sA+sB s5| [i]
mulx s9, s2, s4      | sD s4| s3+s2| sC+s1| s0+sA+sB s5| [i]
movq sD, @r[i+5]     | .. s4| s3+s2| sC+s1| s0+sA+sB s5| [i]
movq @r[i], sD       | .. s4| s3+s2| sC+s1| s0+sA+sB s5+sD [i]
adcx sD, s5          | .. s4| s3+s2| sC+s1| s0+sA+sB' s5 [i]
movq s5, @r[i]       | .. s4| s3+s2| sC+s1| s0+sA+sB' [i+1]
mulx @u[4], s5, sD   | sD| s4+s5| s3+s2| sC+s1| s0+sA+sB' [i+1]
adcx sA, s0          | sD| s4+s5| s3+s2| sC+s1|' s0+sB [i+1]
sA:=v[i+1]
adcx sC, s1          | sD| s4+s5| s3+s2|' s1| s0+sB [i+1] sA=v[i+1]
adox sB, s0          | sD| s4+s5| s3+s2|' s1|" s0 [i+1] sA=v[i+1]
mulx @u[5], sB, sC   | sC sD+sB| s4+s5| s3+s2|' s1|" s0 [i+1] sA=v[i+1]
adcx s3, s2          | sC sD+sB| s4+s5|' s2| s1|" s0 [i+1] sA=v[i+1]
movq @r[i+2], s3     | sC sD+sB| s4+s5|' s2| s1+s3" s0 [i+1] sA=v[i+1]
adox s3, s1          | sC sD+sB| s4+s5|' s2|" s1 s0 [i+1] sA=v[i+1]
movq @r[i+4], s3     | sC sD+sB| s3+s4+s5' s2|" s1 s0 [i+1] sA=v[i+1]
adcx s4, s3          | sC sD+sB|' s3+s5 s2|" s1 s0 [i+1] sA=v[i+1]
movq @r[i+3], s4     | sC sD+sB|' s3+s5 s2+s4" s1 s0 [i+1] sA=v[i+1]
adox s4, s2          | sC sD+sB|' s3+s5" s2 s1 s0 [i+1] sA=v[i+1]
movq @r[i+5], s4     | sC s4+sD+sB' s3+s5" s2 s1 s0 [i+1] sA=v[i+1]
adcx sD, s4          | sC' s4+sB s3+s5" s2 s1 s0 [i+1] sA=v[i+1]
movq sA, dd          | sC' s4+sB s3+s5" s2 s1 s0 [i+1]
'''

"""
i>=2
multiplied by v[0..i-1]
data lies like that: | sC' s4+sB s3+s5" s2 s1 s0 [i] dd=v[i]
                                                     s6=u[0] s7=u[1] s8=u[2] s9=u[3]
"""

g_mul_2 = '''
                     | sC' s4+sB s3+s5" s2 s1 s0 [i]
mulx s6, sA, sD      | sC' s4+sB s3+s5" s2 s1+sD s0+sA [i]
|TODO: extract rp here
adox s5, s3          | sC' s4+sB" s3 s2 s1+sD s0+sA [i]
movq $0, s5          | sC' s4+sB" s3 s2 s1+sD s0+sA [i] s5=0
adcx s5, sC          | sC s4+sB" s3 s2 s1+sD s0+sA [i]
adox sB, s4          | sC" s4 s3 s2 s1+sD s0+sA [i]
mulx s7, s5, sB      | sC" s4 s3 s2+sB s1+sD+s5 s0+sA [i]
movq s2, @r[i+2]     | sC" s4 s3 sB| s1+sD+s5 s0+sA [i]
movq s3, @r[i+3]     | sC" s4 .. sB| s1+sD+s5 s0+sA [i]
mulx s8, s2, s3      | sC" s4 s3| sB+s2| s1+sD+s5 s0+sA [i]
adcx sA, s0          | sC" s4 s3| sB+s2| s1+sD+s5' s0 [i]
movq s0, @r[i]       | sC" s4 s3| sB+s2| s1+sD+s5' [i+1]
mulx s9, s0, sA      | sC" s4+sA s3+s0| sB+s2| s1+sD+s5' [i+1]
adcx sD, s1          | sC" s4+sA s3+s0| sB+s2|' s1+s5 [i+1]
movq $0, sD
adox sD, sC          | sC s4+sA s3+s0| sB+s2|' s1+s5 [i+1]
movq s4, @r[i+4]     | sC sA| s3+s0| sB+s2|' s1+s5 [i+1]
mulx @u[4], s4, sD   | sC+sD sA+s4| s3+s0| sB+s2|' s1+s5 [i+1]
adcx sB, s2          | sC+sD sA+s4| s3+s0|' s2| s1+s5 [i+1]
sB:=v[i+1]           | sC+sD sA+s4| s3+s0|' s2| s1+s5 [i+1] sB=v[i+1]
adox s5, s1          | sC+sD sA+s4| s3+s0|' s2|" s1 [i+1] sB=v[i+1]
mulx @u[5], dd, s5   | s5 sC+sD+dd sA+s4| s3+s0|' s2|" s1 [i+1] sB=v[i+1]
adcx s3, s0          | s5 sC+sD+dd sA+s4|' s0| s2|" s1 [i+1] sB=v[i+1]
movq @r[i+2], s3     | s5 sC+sD+dd sA+s4|' s0| s2+s3" s1 [i+1] sB=v[i+1]
adox s3, s2          | s5 sC+sD+dd sA+s4|' s0|" s2 s1 [i+1] sB=v[i+1]
movq @r[i+4], s3     | s5 sC+sD+dd s3+sA+s4' s0|" s2 s1 [i+1] sB=v[i+1]
adcx sA, s3          | s5 sC+sD+dd' s3+s4 s0|" s2 s1 [i+1] sB=v[i+1]
movq @r[i+3], sA     | s5 sC+sD+dd' s3+s4 s0+sA" s2 s1 [i+1] sB=v[i+1]
adox sA, s0          | s5 sC+sD+dd' s3+s4" s0 s2 s1 [i+1] sB=v[i+1]
adcx sD, sC          | s5' sC+dd s3+s4" s0 s2 s1 [i+1] sB=v[i+1]
xchg sB, dd          | s5' sC+sB s3+s4" s0 s2 s1 [i+1]
'''

"""
old: sC' s4+sB s3+s5" s2 s1 s0
new: s5' sC+sB s3+s4" s0 s2 s1
          0 1 2 3 4 5 6 7 8 9 A B C D                           """
g_perm = '1 2 0 3 C 4 6 7 8 9 A B 5 D'

g_tail = '''
                     | s5' sC+dd s3+s4" s0 s2 s1 [6]
movq rp, sD          | sD points to target
movq @r[0], s7
movq @r[1], s8
movq @r[2], s9
adox s4, s3          | s5' sC+dd" s3 s0 s2 s1 [~6~]
movq $0, s4
adcx s4, s5          | s5 sC+dd" s3 s0 s2 s1 [~6~] s4=0
movq @r[3], sA
movq @r[4], sB
adox sC, dd          | s5" dd s3 s0 s2 s1 [~6~] s4=0
movq @r[5], sC
movq s7, @R[0]
movq s8, @R[1]
movq s9, @R[2]
movq sA, @R[3]
movq sB, @R[4]
movq sC, @R[5]
adox s4, s5          | s5 dd s3 s0 s2 s1 [6]
movq s1, @R[6]
movq s2, @R[7]
movq s0, @R[8]
movq s3, @R[9]
movq dd, @R[10]
movq s5, @R[11]
'''

import os, re, sys
sys.dont_write_bytecode = 1

#TODO: check if all imports needed
import gen_mul4 as P
import gen_mul7_aligned as S
import gen_mul7_t03 as E
import gen_mul6_aligned as W
import gen_mul8_aligned as G

g_iplus_patt = re.compile(r'i\+(.+?)\b')
g_u_patt = re.compile(r'@u\[(.+)\]')
g_r_patt = re.compile(r'@r\[(.+)\]')
g_t_patt = re.compile(r'@R\[(.+)\]')
g_v_patt = re.compile(r'(.+):=v\[(.+)]')
def evaluate_row(i, s):
    m = g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
    s = re.sub(r'\bi\b', '%s' % i, s)

    m = g_u_patt.search(s)
    if m:
        k = int(m.group(1))
        if (k >= 2) and (k <= 5):
            s = s.replace(m.group(), ('%s' % (-104 - 8 * (5 - k))) + '(%rsp)')

    m = g_r_patt.search(s)
    if m:
        k = int(m.group(1))
        if k < 12:
            s = s.replace(m.group(), ('%s' % (-96 + 8 * k)) + '(%rsp)')

    m = g_t_patt.search(s)
    if m:
        k = int(m.group(1))
        if k < 12:
            if k:
                s = s.replace(m.group(), '%s(sD)' % (8 * k))
            else:
                s = s.replace(m.group(), '(sD)')

    m = g_v_patt.match(s)
    if m:
        s = W.extract_v(int(m.group(2)), m.group(1), 8)

    return s

def mul_code(i, jj, p):
    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in jj:
        k = evaluate_row(i, j)
        if k:
            rr.append(k)

    return [E.apply_s_permutation(x, p) for x in rr]

def cook_asm(o, code, xmm_save, var_map):
    P.insert_restore(code, xmm_save)
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    code = P.replace_symbolic_names_wr(code, var_map)

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

def do_it(o):
    preamble = P.cutoff_comments(g_preamble)
    xmm_save = P.save_registers_in_xmm(preamble, 11)
    p = list(range(14))
    code = mul_code(0, preamble, p)
    m1 = P.cutoff_comments(g_mul_1)
    m2 = P.cutoff_comments(g_mul_2)
    code += mul_code(1, m1, p)
    q = [int(x, 16) for x in g_perm.split(' ')]
    for i in range(2, 5):
        code += mul_code(i, m2, p)
        p = P.composition(p, q)
    tail = m2[:-1] + P.cutoff_comments(g_tail)
    code += mul_code(5, tail, p)

    G.save_in_xmm(code, xmm_save)
    P.insert_restore(code, xmm_save)
    cook_asm(o, code, xmm_save, g_var_map)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
