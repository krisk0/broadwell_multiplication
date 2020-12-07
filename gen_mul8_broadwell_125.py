'''
8x8 multiplication targeting Broadwell. 124 ticks on Skylake, 1205 ticks on Ryzen

TODO: improve Slylake throughput by using ymm
'''

"""
      rdi -< rp
      rsi -< up
      rdx -< vp

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w6  w5    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w7  up  rp  dd
"""

g_mul_01='''
vmovdqu 8(dd), v14               | v14=v[1..4]
!save w9
vmovdqu 32(dd), v47              | v47=v[4..7]
movq (dd), dd                    | ready v0
!save w5
mulx (up), w1, w2                | w2 w1
mulx 8(up), w3, w4               | w4 w2+w3 w1
!save w6
mulx 16(up), w5, w6              | w6 w4+w5 w2+w3 w1
!save w8
mulx 24(up), w7, w8              | w8 w6+w7 w4+w5 w2+w3 w1
!save wA
mulx 32(up), w0, w9              | w9 w0+w8 w6+w7 w4+w5 w2+w3 w1
!save wB
mulx 40(up), wA, wB              | wB w9+wA w0+w8 w6+w7 w4+w5 w2+w3 w1
addq w3, w2                      | wB w9+wA w0+w8 w6+w7 w4+w5' w2 w1
movq w1, (rp)                    | wB w9+wA w0+w8 w6+w7 w4+w5' w2 --
movq w2, 8(rp)                   | wB w9+wA w0+w8 w6+w7 w4+w5' .. --
movq v14, w2                     | w2=v[1]
mulx 48(up), w1, w3              | w3 w1+wB w9+wA w0+w8 w6+w7 w4+w5' .. -- w2=v[1]
adcq w5, w4                      | w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. -- w2=v[1]
mulx 56(up), dd, w5              | w5 dd+w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. -- w2=v[1]
adcq w7, w6                      | w5 dd+w3 w1+wB w9+wA w0+w8' w6 w4 .. -- w2=v[1]
movq w4, 16(rp)                  | w5 dd+w3 w1+wB w9+wA w0+w8' w6 .. .. -- w2=v[1]
xchg w2, dd                      | w5 dd+w3 w1+wB w9+wA w0+w8' w6 .. .. --
mulx (up), w4, w7                | w5 w2+w3 w1+wB w9+wA w0+w8' w6 w7: w4: --
adcq w8, w0                      | w5 w2+w3 w1+wB w9+wA' w0 w6 w7: w4: --
adcq wA, w9                      | w5 w2+w3 w1+wB' w9 w0 w6 w7: w4: --
mulx 8(up), w8, wA               | w5 w2+w3 w1+wB' w9 w0 w6+wA w7+w8: w4: --
adcq wB, w1                      | w5 w2+w3' w1 w9 w0 w6+wA w7+w8: w4: --
adcq w3, w2                      | w5' w2 w1 w9 w0 w6+wA w7+w8: w4: --
mulx 16(up), w3, wB              | w5' w2 w1 w9 w0+wB w6+wA+w3 w7+w8: w4: --
adcq $0, w5                      | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8: w4: --
adcx 8(rp), w4                   | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8:' w4 --
movq w4, 8(rp)                   | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8:' {2}
adox 16(rp), w7                  | w5 w2 w1 w9 w0+wB w6+wA+w3" w7+w8' {2}
adox wA, w6                      | w5 w2 w1 w9 w0+wB" w6+w3 w7+w8' {2}
adcx w8, w7                      | w5 w2 w1 w9 w0+wB" w6+w3' w7 {2}
movq w7, 16(rp)                  | w5 w2 w1 w9 w0+wB" w6+w3' .. {2}
mulx 24(up), w7, w8              | w5 w2 w1 w9+w8 w0+wB+w7" w6+w3' .. {2}
mulx 32(up), w4, wA              | w5 w2 w1+wA w9+w8+w4 w0+wB+w7" w6+w3' .. {2}
adox wB, w0                      | w5 w2 w1+wA w9+w8+w4" w0+w7 w6+w3' .. {2}
adcx w6, w3                      | w5 w2 w1+wA w9+w8+w4" w0+w7' w3 .. {2}
movq w3, 24(rp)                  | w5 w2 w1+wA w9+w8+w4" w0+w7' [2] {2}
pextrq $0x1, v14, w3            | w3=v[2]
mulx 40(up), w6, wB            | w5 w2+wB w1+wA+w6 w9+w8+w4" w0+w7' [2] {2} w3=v[2]
adox w9, w8                    | w5 w2+wB w1+wA+w6" w8+w4 w0+w7' [2] {2} w3=v[2]
adcx w7, w0                    | w5 w2+wB w1+wA+w6" w8+w4' w0 [2] {2} w3=v[2]
mulx 48(up), w7, w9            | w5+w9 w2+wB+w7 w1+wA+w6" w8+w4' w0 [2] {2} w3=v[2]
vperm2i128 $0x81,v14,v14,v14
adox wA, w1                    | w5+w9 w2+wB+w7" w1+w6 w8+w4' w0 [2] {2} w3=v[2]
mulx 56(up), wA, dd            | dd w5+w9+wA w2+wB+w7" w1+w6 w8+w4' w0 [2] {2} w3=v[2]
xchg dd, w3                    | w3 w5+w9+wA w2+wB+w7" w1+w6 w8+w4' w0 [2] {2}
adcx w4, w8                    | w3 w5+w9+wA w2+wB+w7" w1+w6' w8 w0 [2] {2}
adox wB, w2                    | w3 w5+w9+wA" w2+w7 w1+w6' w8 w0 [2] {2}
'''

"""
i>=2
multiplied by v[0], .. v[i-1]
data lies like that: s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 [2] {i} dd=v[i]
"""

g_muladd_2 = '''
                         | s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 [2] {i}
mulx (up), s4, sB        | s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 sB: s4: {i}
adcx s6, s1              | s3 s5+s9+sA" s2+s7' s1 s8 s0 sB: s4: {i}
adox s9, s5              | s3" s5+sA s2+s7' s1 s8 s0 sB: s4: {i}
mulx 8(up), s6, s9       | s3" s5+sA s2+s7' s1 s8 s0+s9 sB+s6: s4: {i}
adcx s7,s2               | s3" s5+sA' s2 s1 s8 s0+s9 sB+s6: s4: {i}
movq $0, s7
adox s7, s3              | s3 s5+sA' s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
adcx sA, s5              | s3' s5 s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
movq s5, t0              | s3' t0 s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
mulx 16(up), s5, sA      | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6: s4: {i} s7=0
adox i(rp), s4           | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" s4 {i} s7=0
movq s4, i(rp)           | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" {i+1} s7=0
adcx s7, s3              | s3 t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" {i+1} s7=0
mulx 24(up), s4, s7      | s3 t0 s2 s1+s7 s8+sA+s4 s0+s9+s5 sB+s6:" {i+1}
adox sB, s6              | s3 t0 s2 s1+s7 s8+sA+s4 s0+s9+s5" s6: {i+1}
adox s9, s0              | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5 s6: {i+1}
adcx i+1(rp), s6     | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5' s6 {i+1}
movq s6, i+1(rp)     | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5' .. {i+1}
mulx 32(up), s6, sB  | s3 t0 s2+sB s1+s7+s6 s8+sA+s4" s0+s5' .. {i+1}
adox sA, s8          | s3 t0 s2+sB s1+s7+s6" s8+s4 s0+s5' .. {i+1}
movq t0, sA          | s3 sA s2+sB s1+s7+s6" s8+s4 s0+s5' .. {i+1}
adcx s5, s0          | s3 sA s2+sB s1+s7+s6" s8+s4' s0 .. {i+1}
movq s0, i+2(rp)     | s3 sA s2+sB s1+s7+s6" s8+s4' [2] {i+1}
s9:=v[i+1]
mulx 40(up), s0, s5  | s3 sA+s5 s2+sB+s0 s1+s7+s6" s8+s4' [2] {i+1} s9=v[i+1]
adox s7, s1          | s3 sA+s5 s2+sB+s0" s1+s6 s8+s4' [2] {i+1} s9=v[i+1]
adcx s8, s4          | s3 sA+s5 s2+sB+s0" s1+s6' s4 [2] {i+1} s9=v[i+1]
mulx 48(up), s7, s8  | s3+s8 sA+s5+s7 s2+sB+s0" s1+s6' s4 [2] {i+1} s9=v[i+1]
shift v47
adox sB, s2          | s3+s8 sA+s5+s7" s2+s0 s1+s6' s4 [2] {i+1} s9=v[i+1]
mulx 56(up), sB, dd  | dd s3+s8+sB sA+s5+s7" s2+s0 s1+s6' s4 [2] {i+1} s9=v[i+1]
xchg s9, dd          | s9 s3+s8+sB sA+s5+s7" s2+s0 s1+s6' s4 [2] {i+1}
adcx s6, s1          | s9 s3+s8+sB sA+s5+s7" s2+s0' s1 s4 [2] {i+1}
adox sA, s5          | s9 s3+s8+sB" s5+s7 s2+s0' s1 s4 [2] {i+1}
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
                old: s3 s5+s9+sA" s2+s7 s1+s6' s8 s0
data lies like that: s9 s3+s8+sB" s5+s7 s2+s0' s1 s4 [2] {i} dd=v[i]
'''
#         0 1 2 3 4 5 6 7 8 9 A B
g_perm = '4 2 5 9 6 3 0 7 1 8 B A'

g_tail = '''
                     | s9 s3+s8+sB" s5+s7 s2+s0' s1 s4 {i+3}
movq s4, i+3(rp)     | s9 s3+s8+sB" s5+s7 s2+s0' s1 {i+4}
movq s1, i+4(rp)     | s9 s3+s8+sB" s5+s7 s2+s0' {i+5}
adcx s2, s0          | s9 s3+s8+sB" s5+s7' s0 {i+5}
adox s3, s8          | s9" s8+sB s5+s7' s0 {i+5}
movq $0, s2          | s9" s8+sB s5+s7' s0 {i+5} s2=0
adcx s7, s5          | s9" s8+sB' s5 s0 {i+5} s2=0
movq s0, i+5(rp)     | s9" s8+sB' s5 {i+6} s2=0
movq s5, i+6(rp)     | s9" s8+sB' {i+7} s2=0
adox s2, s9          | s9 s8+sB' {i+7} s2=0
adcx sB, s8          | s9' s8 {i+7} s2=0
movq s8, i+7(rp)     | s9' {i+8} s2=0
adcq $0, s9          | s9 {i+8} s2=0
movq s9, i+8(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def extract_v(i, t):
    if (i == 3):
        return 'movq v14, ' + t
    if (i == 4):
        return 'movq v47, ' + t
    if (i == 5):
        return 'pextrq $0x1, v47, ' + t
    if (i == 6):
        return 'movq v47, ' + t
    if (i == 7):
        return 'pextrq $0x1, v47, ' + t

def shift_v(i):
    if i == 5:
        return 'vperm2i128 $0x81, v47, v47, v47'

def mul1_code(i, jj, p):
    rr = ['# mul_add %s' % i]
    for j in jj:
        if j.find(':=v[i+1]') != -1:
            j = extract_v(i+1, j[:2])
        elif j == 'shift v47':
            j = shift_v(i+1)
        if not j:
            continue
        rr.append(j)

    if i == 7:
        rr += P.cutoff_comments(g_tail)

    # apply permutation p, replace i(rp)
    for y in range(len(rr)):
        src = rr[y]
        for x in range(12):
            a = '%X' % x
            b = '%X' % p[x]
            src = re.sub(r'\bs%s\b' % a, 'w' + b, src)
        src += ' '
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i)) + ' '
        rr[y] = src.rstrip()

    return rr

def cook_asm(name, o, code):
    xmm_save = P.save_registers_in_xmm(code, 9)

    P.insert_restore(code, xmm_save)
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    m = 'rp,rdi up,rsi w7,rcx wB,rbp wA,rbx w9,r12 w8,r13 w6,r14 w5,r15 '
    m += 'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 dd,rdx v14,ymm15 v47,ymm14 t0,xmm13'
    r = {}
    for x in m.split(' '):
        y = x.split(',')
        r[y[0]] = '%' + y[1]
    code = P.replace_symbolic_vars_name(code, r)

    # replace ymm with xmm in all movq
    code = '\n'.join([replace_ymm_by_xmm(x) for x in code.split('\n')])

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(name))
    P.write_asm_inside(o, code + '\nretq')

g_ymm_to_xmm_patt = [re.compile(r'movq .*%ymm.*'), \
        re.compile(r'pextrq \$0x1, %ymm.+')]
def replace_ymm_by_xmm(s):
    for p in g_ymm_to_xmm_patt:
        if p.match(s):
            return s.replace('ymm', 'xmm')
    return s

def do_it(name, o):
    meat = P.cutoff_comments(g_mul_01)
    p = list(range(12))
    meat += mul1_code(2, P.cutoff_comments(g_muladd_2), p)
    q = [int(x, 16) for x in g_perm.split(' ')]
    for i in range(3, 8):
        p = P.composition(p, q)
        meat += mul1_code(i, P.cutoff_comments(g_muladd_2), p)

    cook_asm(name, o, meat)

def swap_adox_adcx(dd):
    rr = []
    for d in dd:
        x = d.replace('adox', 'ADCX').replace('adcx', 'adox').\
                replace('ADCX', 'adcx')
        rr.append(x)
    return rr

with open(sys.argv[1], 'wb') as g_out:
    do_it(sys.argv[1], g_out)
