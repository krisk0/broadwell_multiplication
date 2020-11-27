"""
      rdi -< rp
      rsi -< up
      rdx -< (vp)

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w6  w5    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w7  up  rp  dd
"""

g_mul0='''
!save w8
movq dd, w0
movq (dd), dd                    | ready v0
!save w5
vmovdqu 8(w0), v14               | ready v[1..4]
mulx (up), w1, w2                | w2 w1
mulx 8(up), w3, w4               | w4 w2+w3 w1
!save w6
vpxor vZ, vZ, vZ                 | will need zero later
mulx 16(up), w5, w6              | w6 w4+w5 w2+w3 w1
mulx 24(up), w7, w8              | w8 w6+w7 w4+w5 w2+w3 w1
!save w9
vmovdqu 32(w0), v47              | ready v[4..7]
!save wA
mulx 32(up), w0, w9              | w9 w0+w8 w6+w7 w4+w5 w2+w3 w1
!save wB
mulx 40(up), wA, wB              | wB w9+wA w0+w8 w6+w7 w4+w5 w2+w3 w1
addq w3, w2                      | wB w9+wA w0+w8 w6+w7 w4+w5' w2 w1
movq w1, (rp)                    | wB w9+wA w0+w8 w6+w7 w4+w5' w2 --
mulx 48(up), w1, w3              | w3 w1+wB w9+wA w0+w8 w6+w7 w4+w5' w2 --
adcq w5, w4                      | w3 w1+wB w9+wA w0+w8 w6+w7' w4 w2 --
movq w2, 8(rp)                   | w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. --
mulx 56(up), w2, w5              | w5 w2+w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. --
movq v14, dd                     | ready v[1]
adcq w7, w6                      | w5 w2+w3 w1+wB w9+wA w0+w8' w6 w4 .. --
movq w4, 16(rp)                  | w5 w2+w3 w1+wB w9+wA w0+w8' w6 .. .. --
mulx (up), w4, w7                | w5 w2+w3 w1+wB w9+wA w0+w8' w6 w7: w4: --
adcq w8, w0                      | w5 w2+w3 w1+wB w9+wA' w0 w6 w7: w4: --
adcq wA, w9                      | w5 w2+w3 w1+wB' w9 w0 w6 w7: w4: --
mulx 8(up), w8, wA               | w5 w2+w3 w1+wB' w9 w0 w6+wA w7+w8: w4: --
adcq wB, w1                      | w5 w2+w3' w1 w9 w0 w6+wA w7+w8: w4: --
adcq w3, w2                      | w5' w2 w1 w9 w0 w6+wA w7+w8: w4: --
mulx 16(up), w3, wB              | w5' w2 w1 w9 w0+wB w3+w6+wA w7+w8: w4: --
adcq $0, w5                      | w5 w2 w1 w9 w0+wB w3+w6+wA w7+w8: w4: --
addq w4, 8(rp)                   | w5 w2 w1 w9 w0+wB w3+w6+wA w7+w8': -- --
movq vZ, w4                      | w4 = 0
adcq w8, 16(rp)                  | w5 w2 w1 w9 w0+wB w3+w6+wA' w7: -- --
adcq wA, w6                      | w5 w2 w1 w9 w0+wB' w3+w6 w7: -- --
mulx 24(up), w8, wA              | w5 w2 w1 w9+wA w0+w8+wB' w3+w6 w7: -- --
adcq wB, w0                      | w5 w2 w1 w9+wA' w0+w8 w3+w6 w7: -- --
movq 16(rp), wB                  | w5 w2 w1 w9+wA' w0+w8 w3+w6 w7+wB -- --
adcq $0, w4                      | w5 w2 w1 w4+w9+wA w0+w8 w3+w6 w7+wB {2}
xor %edx, %edx
movq v14, dd                     | ready v[1]
adox wB, w7                      | w5 w2 w1 w4+w9+wA w0+w8 w3+w6" w7 {2}
adox w6, w3                      | w5 w2 w1 w4+w9+wA w0+w8" w3 w7 {2}
adox w8, w0                      | w5 w2 w1 w4+w9+wA" w0 w3 w7 {2}
mulx 32(up), w6, wB              | w5 w2 w1+wB w4+w6+w9+wA" w0 w3 w7 {2}
adox wA, w9                      | w5 w2 w1+wB" w4+w6+w9 w0 w3 w7 {2}
mulx 40(up), w8, wA              | w5 w2+wA w1+w8+wB" w4+w6+w9 w0 w3 w7 {2}
adcx w9, w4                      | w5 w2+wA w1+w8+wB'" w4+w6 w0 w3 w7 {2}
movq w7, 16(rp)                  | w5 w2+wA w1+w8+wB'" w4+w6 w0 w3 .. {2}
mulx 48(up), w7, w9              | w5+w9 w2+w7+wA w1+w8+wB'" w4+w6 w0 w3 .. {2}
adox wB, w1                      | w5+w9 w2+w7+wA" w1+w8' w4+w6 w0 w3 .. {2}
adox wA, w2                      | w5+w9" w2+w7 w1+w8' w4+w6 w0 w3 .. {2}
mulx 56(up), wA, wB              | wB w5+w9+wA" w2+w7 w1+w8' w4+w6 w0 w3 .. {2}
vpextrq $0x1, v14, dd            | ready v[2]
adcx w8, w1                      | wB w5+w9+wA" w2+w7' w1 w4+w6 w0 w3 .. {2}
movq vZ, w8
adcx w7, w2                      | wB w5+w9+wA'" w2 w1 w4+w6 w0 w3 .. {2}
adox w9, w5                      | wB" w5+wA' w2 w1 w4+w6 w0 w3 .. {2}

vperm2i128 $0x81, v14, v14, v14  | shift away v[1..2]
mulx (up), w7, w9                | wB" w5+wA' w2 w1 w4+w6 w0 w3+w9 w7: {2}
adox w8, wB                      | wB w5+wA' w2 w1 w4+w6 w0 w3+w9 w7: {2}
adcx wA, w5                      | wB' w5 w2 w1 w4+w6 w0 w3+w9 w7: {2}
adcx w8, wB                      | wB w5 w2 w1 w4+w6 w0 w3+w9 w7: {2}
mulx 8(up), w8, wA               | wB w5 w2 w1 w4+w6 w0+wA w3+w8+w9 w7: {2}
movq wB, t0                      | t0 w5 w2 w1 w4+w6 w0+wA w3+w8+w9 w7: {2}
movq 16(rp), wB                  | t0 w5 w2 w1 w4+w6 w0+wA w3+w8+w9 w7+wB {2}
adcx w9, w3                      | t0 w5 w2 w1 w4+w6 w0+wA' w3+w8 w7+wB {2}
movq t0, w9                      | w9 w5 w2 w1 w4+w6 w0+wA' w3+w8 w7+wB {2}
adox wB, w7                      | w9 w5 w2 w1 w4+w6 w0+wA' w3+w8" w7 {2}
movq w7, 16(rp)                  | w9 w5 w2 w1 w4+w6 w0+wA' w3+w8" {3}
mulx 16(up), w7, wB              | w9 w5 w2 w1 w4+w6+wB w0+wA+w7' w3+w8" {3}
adox w8, w3                      | w9 w5 w2 w1 w4+w6+wB w0+wA+w7'" w3 {3}
adcx wA, w0                      | w9 w5 w2 w1 w4+w6+wB' w0+w7" w3 {3}
mulx 24(up), w8, wA              | w9 w5 w2 w1+wA w4+w6+wB+w8' w0+w7" w3 {3}
movq w3, 24(rp)                  | w9 w5 w2 w1+wA w4+w6+wB+w8' w0+w7" .. {3}
adox w7, w0                      | w9 w5 w2 w1+wA w4+w6+wB+w8'" w0 .. {3}
mulx 32(up), w3, w7              | w9 w5 w2+w7 w1+wA+w3 w4+w6+wB+w8'" w0 .. {3}
adcx w6, w4                      | w9 w5 w2+w7 w1+wA+w3' w4+wB+w8" w0 .. {3}
movq w0, 32(rp)                  | w9 w5 w2+w7 w1+wA+w3' w4+wB+w8" .. .. {3}
mulx 40(up), w0, w6              | w9 w5+w6 w2+w7+w0 w1+wA+w3' w4+wB+w8" .. .. {3}
adox wB, w4
adcx wA, w1                      | w9 w5+w6 w2+w7+w0' w1+w3" w4+w8 .. .. {3}
mulx 48(up), wA, wB              | w9+wB w5+w6+wA w2+w7+w0' w1+w3" w4+w8 .. .. {3}
adox w3, w1                      | w9+wB w5+w6+wA w2+w7+w0'" w1 w4+w8 .. .. {3}
adcx w7, w2                      | w9+wB w5+w6+wA' w2+w0" w1 w4+w8 .. .. {3}
mulx 56(up), w3, w7              | w7 w9+wB+w3 w5+w6+wA' w2+w0" w1 w4+w8 .. .. {3}
movq v14, dd                     | ready v[3]
adox w2, w0                      | w7 w9+wB+w3 w5+w6+wA'" w0 w1 w4+w8 .. .. {3}
movq vZ, w2                      | w2=0
adcx w6, w5                      | w7 w9+wB+w3' w5+wA" w0 w1 w4+w8 .. .. {3}
adcx wB, w9                      | w7' w9+w3 w5+wA" w0 w1 w4+w8 .. .. {3}
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
dd = v[i]
v[i+1] can be extracted with single instruction
data lies like that: s7' s3+s9 s5+sA" s0 s1 s4+s8 .. .. {i}
overflow flag = 0
s2 = 0
'''

g_muladd_3='''                | s7' s3+s9 s5+sA" s0 s1 s4+s8 .. .. {i} s2=0
mulx (up), s6, sB             | s7' s3+s9 s5+sA" s0 s1 s4+s8 sB: s6: {i} s2=0
adox sA, s5                   | s7' s3+s9" s5 s0 s1 s4+s8 sB: s6: {i} s2=0
adcx s2, s7                   | s7 s3+s9" s5 s0 s1 s4+s8 sB: s6: {i} s2=0
adox s9, s3                   | s7" s3 s5 s0 s1 s4+s8 sB: s6: {i} s2=0
mulx 8(up), s9, sA            | s7" s3 s5 s0 s1 s4+s8+sA sB+s9: s6: {i} s2=0
adox s2, s7                   | s7 s3 s5 s0 s1 s4+s8+sA sB+s9: s6: {i} s2=0
adcx s8, s4                   | s7 s3 s5 s0 s1' s4+sA sB+s9: s6: {i} s2=0
mulx 16(up), s2, s8           | s7 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6: {i} 
movq s7, t0                   | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6: {i} 
movq i(rp), s7                | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6+s7 {i} 
adox s7, s6                   | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9": s6 {i} 
movq i+1(rp), s7              | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s7+s9" s6 {i} 
adox sB, s7                   | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 s6 {i} 
movq s6, i(rp)                | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 .. {i} 
movq vZ, sB                   | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 .. {i} sB=0
movq s3, t1                   | t0 t1 s5 s0 s1+s8' s4+sA+s2" s7+s9 .. {i} sB=0
mulx 24(up), s3, s6           | t0 t1 s5 s0+s6 s1+s8+s3' s4+sA+s2" s7+s9 .. {i} sB=0
adox sA, s4                   | t0 t1 s5 s0+s6 s1+s8+s3'" s4+s2 s7+s9 .. {i} sB=0
adcx s8, s1                   | t0 t1 s5 s0+s6' s1+s3" s4+s2 s7+s9 .. {i} sB=0
mulx 32(up), s8, sA           | t0 t1 s5+sA s0+s6+s8' s1+s3" s4+s2 s7+s9 .. {i} sB=0
adcx sB, sB                   | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2 s7+s9 .. {i} sB=0
adcx s9, s7                   | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2' s7 .. {i}
movq s7, i+1(rp)              | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2' .. .. {i}
mulx 40(up), s7, s9           | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3" s4+s2' .. .. {i}
adcx s4, s2                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' s2 .. .. {i}
movq s2, i+2(rp)              | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' [3] {i}
movq vZ, s2                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' [3] {i} s2=0
adox s3, s1                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB" s1' [3] {i} s2=0
adox s6, s0                   | t0 t1+s9 s5+sA+s7" s0+s8+sB s1' [3] {i} s2=0
mulx 48(up), s3, s6           | t0+s6 t1+s9+s3 s5+sA+s7" s0+s8+sB s1' [3] {i} s2=0
adcx s2, s1                   | t0+s6 t1+s9+s3 s5+sA+s7" s0+s8+sB' s1 [3] {i} s2=0
mulx 56(up), s2, s4           | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7" s0+s8+sB' s1 [3] {i} 
movq s1, i+2(rp)              | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7" s0+s8+sB' [4] {i}
movq vZ, s1
adcx s8, s0                   | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7"' s0+sB [4] {i} s1=0
movq t1, s8                   | s4 t0+s6+s2 s9+s3+s8 s5+sA+s7"' s0+sB [4] {i} s1=0
adox sA, s5                   | s4 t0+s6+s2 s9+s3+s8" s5+s7' s0+sB [4] {i} s1=0
extract v[i+1]
movq t0, sA                   | s4 s6+s2+sA s9+s3+s8" s5+s7' s0+sB [4] {i} s1=0
adcx s7, s5                   | s4 s6+s2+sA s9+s3+s8"' s5 s0+sB [4] {i} s1=0
adox s9, s3                   | s4 s6+s2+sA" s3+s8' s5 s0+sB [4] {i} s1=0
adox s6, s2                   | s4" s2+sA s3+s8' s5 s0+sB [4] {i} s1=0
adcx s8, s3                   | s4" s2+sA' s3 s5 s0+sB [4] {i} s1=0
adox s1, s4                   | s4 s2+sA' s3 s5 s0+sB [4] {i} s1=0
adcx sA, s2                   | s4' s2 s3 s5 s0+sB [4] {i} s1=0
'''

"""
i >= 4
s2=0
dd=v[i]
multiplied by v[0], .. v[i-1]
v[i+1] can be extracted with single instruction
data lies like that: s4' s2 s3 s5 s0+sB .. .. .. {i-1} s1=0
"""

g_tail = '''
movq $0, 40(rp)
movq $0, 48(rp)
movq $0, 56(rp)
movq $0, 64(rp)
movq $0, 72(rp)
movq $0, 80(rp)
movq $0, 88(rp)
movq $0, 96(rp)
movq $0, 104(rp)
movq $0, 112(rp)
movq $0, 120(rp)
!restore wB
!restore wA
!restore w9
!restore w8
!restore w6
!restore w5
'''

g_tail_no = '''
                      | s3 = sB = 0
                      | s5 sA+s4 s8+s9' s6 s0" -- -- -- {8}
!restore s7
!restore sB
adox s3, s0
adcx s9, s8           | s5 sA+s4' s8 s6" s0 -- -- -- {8}
!restore s9
movq s0, i+4(rp)      | s5 sA+s4' s8 s6" -- -- -- -- {8}
!restore s0
movq s5, s1           | s1 sA+s4' s8 s6" -- -- -- -- {8}
!restore s5
adox s3, s6
adcx sA, s4           | s1' s4 s8" s6 -- -- -- -- {8}
!restore sA
movq s6, i+5(rp)      | s1' s4 s8" -- -- -- -- -- {8}
adox s3, s8
!restore s6
adox s3, s4           | s1'" s4 s8 -- -- -- -- -- {8}
movq s8, i+6(rp)      | s1'" s4 -- -- -- -- -- -- {8}
!restore s8
adcx s3, s1           | s1" s4 -- -- -- -- -- -- {8}
movq s4, i+7(rp)      | s1" -- -- -- -- -- -- -- {8}
adox s3, s1
movq s1, i+8(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul8_store1 as E

def extract_code(i):
    if i in [4, 6]:
        return 'movq v47, dd'
    if i in [5, 7]:
        return 'vpextrq $0x1, v47, dd'
    return ''

def mul1_code(i, jj, p):
    rr = []
    for j in jj:
        if j == 'extract v[i+1]':
            rr.append(extract_code(i + 1))
            continue
        if j == 'shift v47':
            # only needed once for i = 4
            if i == 4:
                rr.append('vperm2i128 $0x81,v47,v47,v47')
            continue
        rr.append(j)

    if i == 7:
        rr = rr[:-3] + P.cutoff_comments(g_tail)

    # apply permutation p
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

def cook_asm(o, code):
    xmm_save = P.save_registers_in_xmm(code, 10)

    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))
    code = '\n'.join([x for x in code.split('\n') if x.find('!restore') == -1])

    m = 'rp,rdi up,rsi w7,rcx wB,rbp wA,rbx w9,r12 w8,r13 w6,r14 w5,r15 '
    m += 'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 dd,rdx vZ,xmm15 v14,ymm14 v47,ymm13 '
    m += 't0,ymm12 t1,ymm11'
    r = {}
    for x in m.split(' '):
        y = x.split(',')
        r[y[0]] = '%' + y[1]
    code = P.replace_symbolic_vars_name(code, r)

    # replace ymm with xmm in all movq and vpextrq
    code = '\n'.join([replace_ymm_by_xmm(x) for x in code.split('\n')])

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, 'mul8_zen')
    P.write_asm_inside(o, code + '\nretq')

g_ymm_to_xmm_patt = [re.compile(r'movq .*%ymm.*'), \
        re.compile(r'vpextrq \$0x1, %ymm.+')]
def replace_ymm_by_xmm(s):
    for p in g_ymm_to_xmm_patt:
        if p.match(s):
            return s.replace('ymm', 'xmm')
    return s

def do_it(o):
    meat = P.cutoff_comments(g_mul0)
    m3 = P.cutoff_comments(g_muladd_3)
    #muladd = P.cutoff_comments(g_muladd)

    p = list(range(12))
    meat += mul1_code(3, m3, p)
    meat += P.cutoff_comments(g_tail)
    '''
    u = [int(y) for y in g_permutation.split(' ')]
    for i in range(3, 8):
        meat += mul1_code(i, muladd, p)
        p = P.composition(p, u)
    '''

    cook_asm(o, meat)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
