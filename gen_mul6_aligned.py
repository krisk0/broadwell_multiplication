'''
6x6 multiplication that uses xmm to store v[] and avoids movdqu. 66 ticks on Skylake,
 61 on Ryzen

Ticks reported by benchm48_toom22_t.exe on Ryzen when using this subroutine: 2880.
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_aligned as S
import gen_mul7_t03 as E

g_preamble = '''
vzeroupper
movq dd, w0
and $0xF, dd
!save w6
movq (w0), dd
jz align0
movdqa 8(w0), t0         | t0=v[1..2]
movdqa 24(w0), t1        | t1=v[3..4]
!save w7
movq 40(w0), t2          | t2=v[5]
'''

g_load0 = '''
movq 8(w0), t0           | t0=v[1]
movdqa 16(w0), t1        | t1=v[2..3]
!save w7
movdqa 32(w0), t2        | t2=v[4..5]
'''

g_mul01 = '''
!save w8
mulx (up), w0, w1        | w1 w0
!save w9
mulx 8(up), w2, w3       | w3 w1+w2 w0
!save wA
wA:=v[1]
mulx 16(up), w4, w5      | w5 w3+w4 w1+w2 w0
!save wB
mulx 24(up), w6, w7      | w7 w5+w6 w3+w4 w1+w2 w0
mulx 32(up), w8, w9      | w9 w7+w8 w5+w6 w3+w4 w1+w2 w0
movq w0, (rp)            | w9 w7+w8 w5+w6 w3+w4 w1+w2 ..
mulx 40(up), w0, wB      | wB w9+w0 w7+w8 w5+w6 w3+w4 w1+w2 ..
movq wA, dd
adcx w2, w1              | wB w9+w0 w7+w8 w5+w6 w3+w4' w1 ..
mulx (up), w2, wA        | wB w9+w0 w7+w8 w5+w6 w3+w4+wA' w1+w2 ..
adcx w4, w3              | wB w9+w0 w7+w8 w5+w6' w3+wA w1+w2 ..
adcx w6, w5              | wB w9+w0 w7+w8' w5 w3+wA w1+w2 ..
mulx 8(up), w4, w6       | wB w9+w0 w7+w8' w5+w6 w3+wA+w4 w1+w2 ..
adcx w8, w7              | wB w9+w0' w7 w5+w6 w3+wA+w4 w1+w2 ..
adox w2, w1              | wB w9+w0' w7 w5+w6 w3+wA+w4" w1 ..
movq w1, 8(rp)           | wB w9+w0' w7 w5+w6 w3+wA+w4" [2]
w1:=v[2]
mulx 16(up), w2, w8      | wB w9+w0' w7+w8 w5+w6+w2 w3+wA+w4" [2] w1=v[2]
adcx w9, w0              | wB' w0 w7+w8 w5+w6+w2 w3+wA+w4" [2] w1=v[2]
adox wA, w3              | wB' w0 w7+w8 w5+w6+w2" w3+w4 [2] w1=v[2]
mulx 24(up), w9, wA      | wB' w0+wA w7+w8+w9 w5+w6+w2" w3+w4 [2] w1=v[2]
adox w6, w5              | wB' w0+wA w7+w8+w9" w5+w2 w3+w4 [2] w1=v[2]
movq $0, w6
adcx w6, wB              | wB w0+wA w7+w8+w9" w5+w2 w3+w4 [2] w1=v[2]
adox w8, w7              | wB w0+wA" w7+w9 w5+w2 w3+w4 [2] w1=v[2]
mulx 32(up), w6, w8      | wB+w8 w0+wA+w6" w7+w9 w5+w2 w3+w4 [2] w1=v[2]
adcx w4, w3              | wB+w8 w0+wA+w6" w7+w9 w5+w2' w3 [2] w1=v[2]
mulx 40(up), w4, dd      | dd wB+w8+w4 w0+wA+w6" w7+w9 w5+w2' w3 [2] w1=v[2]
adox wA, w0              | dd wB+w8+w4" w0+w6 w7+w9 w5+w2' w3 [2]
adcx w5, w2              | dd wB+w8+w4" w0+w6 w7+w9' w2 w3 [2]
xchg dd, w1              | w1 wB+w8+w4" w0+w6 w7+w9' w2 w3 [2]
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that: s1 sB+s8+s4" s0+s6 s7+s9' s2 s3 [i] dd=v[i]
'''

g_mul2 = '''             | s1 sB+s8+s4" s0+s6 s7+s9' s2 s3 [i]
mulx (up), s5, sA        | s1 sB+s8+s4" s0+s6 s7+s9' s2+sA s3+s5 [i]
adox sB, s8              | s1" s8+s4 s0+s6 s7+s9' s2+sA s3+s5 [i]
movq $0, sB
adcx s9, s7              | s1" s8+s4 s0+s6' s7 s2+sA s3+s5 [i]
adox sB, s1              | s1 s8+s4 s0+s6' s7 s2+sA s3+s5 [i]
mulx 8(up), s9, sB       | s1 s8+s4 s0+s6' s7+sB s2+sA+s9 s3+s5 [i]
adcx s6, s0              | s1 s8+s4' s0 s7+sB s2+sA+s9 s3+s5 [i]
adox s5, s3              | s1 s8+s4' s0 s7+sB s2+sA+s9" s3 [i]
movq s3, i(rp)           | s1 s8+s4' s0 s7+sB s2+sA+s9" [i+1]
s6:=v[i+1]               | s1 s8+s4' s0 s7+sB s2+sA+s9" [i+1] s6=v[i+1]
mulx 16(up), s3, s5      | s1 s8+s4' s0+s5 s7+sB+s3 s2+sA+s9" [i+1] s6=v[i+1]
adcx s8, s4              | s1' s4 s0+s5 s7+sB+s3 s2+sA+s9" [i+1] s6=v[i+1]
movq $0, s8
adox sA, s2              | s1' s4 s0+s5 s7+sB+s3" s2+s9 [i+1] s6=v[i+1]
adcx s8, s1              | s1 s4 s0+s5 s7+sB+s3" s2+s9 [i+1] s6=v[i+1]
mulx 24(up), s8, sA      | s1 s4+sA s0+s5+s8 s7+sB+s3" s2+s9 [i+1] s6=v[i+1]
adox sB, s7              | s1 s4+sA s0+s5+s8" s7+s3 s2+s9 [i+1] s6=v[i+1]
adcx s9, s2              | s1 s4+sA s0+s5+s8" s7+s3' s2 [i+1] s6=v[i+1]
mulx 32(up), s9, sB      | s1+sB s4+sA+s9 s0+s5+s8" s7+s3' s2 [i+1] s6=v[i+1]
adox s5, s0              | s1+sB s4+sA+s9" s0+s8 s7+s3' s2 [i+1] s6=v[i+1]
mulx 40(up), s5, dd      | dd s1+sB+s5 s4+sA+s9" s0+s8 s7+s3' s2 [i+1] s6=v[i+1]
adcx s7, s3              | dd s1+sB+s5 s4+sA+s9" s0+s8' s3 s2 [i+1] s6=v[i+1]
adox sA, s4              | dd s1+sB+s5" s4+s9 s0+s8' s3 s2 [i+1] s6=v[i+1]
xchg dd, s6              | s6 s1+sB+s5" s4+s9 s0+s8' s3 s2 [i+1]
'''

g_tail = '''             | dd s1+sB+s5" s4+s9 s0+s8' s3 s2 [i+1]
movq s2, i+1(rp)         | dd s1+sB+s5" s4+s9 s0+s8' s3 [i+2]
movq s3, i+2(rp)         | dd s1+sB+s5" s4+s9 s0+s8' [i+3]
movq $0, s2              | dd s1+sB+s5" s4+s9 s0+s8' [i+3] s2=0
movq s1, s3              | dd s3+sB+s5" s4+s9 s0+s8' [i+3] s2=0
adcx s8, s0              | dd s3+sB+s5" s4+s9' s0 [i+3] s2=0
adox sB, s3              | dd" s3+s5 s4+s9' s0 [i+3] s2=0
movq s0, i+3(rp)         | dd" s3+s5 s4+s9' [i+4] s2=0
adcx s9, s4              | dd" s3+s5' s4 [i+4] s2=0
adox s2, dd              | dd s3+s5' s4 [i+4] s2=0
movq s4, i+4(rp)         | dd s3+s5' [i+5] s2=0
adcx s5, s3              | dd' s3 [i+5] s2=0
movq s3, i+5(rp)         | dd' [i+6] s2=0
adcq $0, dd
movq dd, i+6(rp)
'''

"""
s1 sB+s8+s4" s0+s6 s7+s9' s2 s3
s6 s1+sB+s5" s4+s9 s0+s8' s3 s2
          0 1 2 3 4 5 6 7 8 9 A B"""
g_perm = '4 6 3 2 5 7 9 0 1 8 A B'

def extract_v(i, t, align):
    if i == 1:
        return 'movq t0, ' + t
    if align == 8:
        if (i == 2):
            return 'pextrq $0x1, t0, ' + t
        if (i == 3):
            return 'movq t1, ' + t
        if (i == 4):
            return 'pextrq $0x1, t1, ' + t
        if (i == 5):
            return 'movq t2, ' + t
    if (i == 2):
        return 'movq t1, ' + t
    if (i == 3):
        return 'pextrq $0x1, t1, ' + t
    if (i == 4):
        return 'movq t2, ' + t
    if (i == 5):
        return 'pextrq $0x1, t2, ' + t

g_patt = re.compile(r'(.+):=v\[(.+)\]')
def mul_code(i, jj_arg, p, align):
    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    if i == 5:
        jj = jj_arg[:-1] + P.cutoff_comments(g_tail)
    else:
        jj = jj_arg

    for j in jj:
        m = g_patt.match(j)
        if m:
            u,v = m.group(1),m.group(2)
            if v == 'i+1':
                k = extract_v(i + 1, u, align)
            else:
                k = extract_v(int(v), u, align)
            if k:
                rr.append(k)
            continue
        rr.append(j)

    for y in range(len(rr)):
        src = E.apply_s_permutation(rr[y], p)
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i))
        rr[y] = src.rstrip()

    return rr

def alignment_code(shift):
    p = list(range(12))
    r = mul_code(0, P.cutoff_comments(g_mul01), p, shift)
    q = [int(x, 16) for x in g_perm.split(' ')]
    m = P.cutoff_comments(g_mul2)
    for i in range(2, 6):
        r += mul_code(i, m, p, shift)
        p = P.composition(p, q)
    return r

def do_it(o):
    code = P.cutoff_comments(g_preamble)
    mul_01 = P.cutoff_comments(g_mul01)
    xmm_save = P.save_registers_in_xmm(code + mul_01, 9)
    code += alignment_code(8) + ['retq', 'align0:']
    P.insert_restore(code, xmm_save)
    code += P.cutoff_comments(g_load0)
    code += alignment_code(0)

    P.save_in_xmm(code, xmm_save)
    P.insert_restore(code, xmm_save)
    S.cook_asm(o, code, xmm_save)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
