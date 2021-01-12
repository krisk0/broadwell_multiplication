'''
5x5 multiplication targeting Broadwell and Ryzen.
'''

g_preamble = '''
vzeroupper
!save w6
movq dd, w0
and $0xF, dd
movq (w0), dd
jz align0
movdqa 8(w0), t0         | t0=v[1..2]
!save w7
movdqa 24(w0), t1        | t1=v[3..4]
'''

g_load0 = '''
movq 8(w0), t0           | t0=v[1]
movdqa 16(w0), t1        | t1=v[2..3]
!save w7
movq 32(w0), t2
'''

g_mul_01 = '''
mulx (up), w0, w1        | w1 w0
!save w8
mulx 8(up), w2, w3       | w3 w1+w2 w0
!save w9
w6:=v[1]
mulx 16(up), w4, w5      | w5 w3+w4 w1+w2 w0
!save wA
mulx 24(up), w8, w7      | w7 w5+w8 w3+w4 w1+w2 w0
movq w0, rp[0]           | w7 w5+w8 w3+w4 w1+w2 [1]
!save wB
mulx 32(up), w0, w9      | w9 w7+w0 w5+w8 w3+w4 w1+w2 [1]
movq w6, dd
w6:=v[2]
adcx w2, w1              | w9 w7+w0 w5+w8 w3+w4' w1 [1]
mulx (up), w2, wA        | w9 w7+w0 w5+w8 w3+w4+wA' w1+w2 [1]
adcx w4, w3              | w9 w7+w0 w5+w8' w3+wA w1+w2 [1]
mulx 8(up), w4, wB       | w9 w7+w0 w5+w8+wB' w3+wA+w4 w1+w2 [1]
adcx w8, w5              | w9 w7+w0' w5+wB w3+wA+w4 w1+w2 [1]
adcx w7, w0              | w9' w0 w5+wB w3+wA+w4 w1+w2 [1]
mulx 16(up), w7, w8      | w9' w0+w8 w5+wB+w7 w3+wA+w4 w1+w2 [1]
adox w2, w1              | w9' w0+w8 w5+wB+w7 w3+wA+w4" w1 [1]
movq w1, rp[1]           | w9' w0+w8 w5+wB+w7 w3+wA+w4" [2]
mulx 24(up), w1, w2      | w9+w2' w0+w8+w1 w5+wB+w7 w3+wA+w4" [2]
adox wA, w3              | w9+w2' w0+w8+w1 w5+wB+w7" w3+w4 [2]
movq w6, rp[2]
mulx 32(up), w6, wA      | wA w9+w2+w6' w0+w8+w1 w5+wB+w7" w3+w4 [2]
movq rp[2], dd
adox wB, w5              | wA w9+w2+w6' w0+w8+w1" w5+w7 w3+w4 [2]
movq w4, rp[2]           | wA w9+w2+w6' w0+w8+w1" w5+w7 w3| [2]
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that: sA s9+s2+s6' s0+s8+s1" s5+s7 s3| [i] dd=v[i]
'''

g_mul_2 = '''
                         | sA s9+s2+s6' s0+s8+s1" s5+s7 s3| [i]
mulx (up), s4, sB        | sA s9+s2+s6' s0+s8+s1" s5+s7+sB s3+s4| [i]
adcx s2, s9              | sA' s9+s6 s0+s8+s1" s5+s7+sB s3+s4| [i]
adox s8, s0              | sA' s9+s6" s0+s1 s5+s7+sB s3+s4| [i]
movq $0, s2
adcx s2, sA              | sA s9+s6" s0+s1 s5+s7+sB s3+s4| [i]
mulx 8(up), s2, s8       | sA s9+s6" s0+s1+s8 s5+s7+sB+s2 s3+s4| [i]
adox s9, s6              | sA" s6 s0+s1+s8 s5+s7+sB+s2 s3+s4| [i]
movq s5, rp[i+1]         | sA" s6 s0+s1+s8 s7+sB+s2| s3+s4| [i]
mulx 16(up), s5, s9      | sA" s6+s9 s0+s1+s8+s5 s7+sB+s2| s3+s4| [i]
adcx s4, s3              | sA" s6+s9 s0+s1+s8+s5 s7+sB+s2|' s3| [i]
movq $0, s4
adox s4, sA              | sA s6+s9 s0+s1+s8+s5 s7+sB+s2|' s3| [i]
movq rp[i], s4           | sA s6+s9 s0+s1+s8+s5 s7+sB+s2|' s3+s4 [i]
adcx sB, s7              | sA s6+s9 s0+s1+s8+s5' s7+s2| s3+s4 [i]
sB:=v[i+1]               | sA s6+s9 s0+s1+s8+s5' s7+s2| s3+s4 [i] sB=v[i+1]
adox s4, s3              | sA s6+s9 s0+s1+s8+s5' s7+s2|" s3 [i] sB=v[i+1]
movq s3, rp[i]           | sA s6+s9 s0+s1+s8+s5' s7+s2|" [i+1] sB=v[i+1]
mulx 24(up), s3, s4      | sA+s4 s6+s9+s3 s0+s1+s8+s5' s7+s2|" [i+1] sB=v[i+1]
adcx s1, s0              | sA+s4 s6+s9+s3' s0+s8+s5 s7+s2|" [i+1] sB=v[i+1]
adox s7, s2              | sA+s4 s6+s9+s3' s0+s8+s5" s2| [i+1] sB=v[i+1]
mulx 32(up), s1, s7      | s7 sA+s4+s1 s6+s9+s3' s0+s8+s5" s2| [i+1] sB=v[i+1]
adcx s9, s6              | s7 sA+s4+s1' s6+s3 s0+s8+s5" s2| [i+1] sB=v[i+1]
adox s8, s0              | s7 sA+s4+s1' s6+s3" s0+s5 s2| [i+1] sB=v[i+1]
adcx sA, s4              | s7' s4+s1 s6+s3" s0+s5 s2| [i+1] sB=v[i+1]
adox s6, s3              | s7' s4+s1" s3 s0+s5 s2| [i+1] sB=v[i+1]
movq sB, dd              | s7' s4+s1" s3 s0+s5 s2| [i+1] dd=v[i+1]
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
data lies like that: s7' s4+s1" s3 s0+s5 s2| [i] dd=v[i]
'''

g_mul_3 = '''
                         | s7' s4+s1" s3 s0+s5 s2| [i]
mulx (up), s6, s8        | s7' s4+s1" s3 s0+s5+s8 s2+s6| [i]
mulx 8(up), s9, sA       | s7' s4+s1" s3+sA s0+s5+s8+s9 s2+s6| [i]
movq $0, sB
adcx sB, s7              | s7 s4+s1" s3+sA s0+s5+s8+s9 s2+s6| [i]
movq rp[i], sB           | s7 s4+s1" s3+sA s0+s5+s8+s9 sB+s2+s6 [i]
adox s4, s1              | s7" s1 s3+sA s0+s5+s8+s9 sB+s2+s6 [i]
adcx sB, s2              | s7" s1 s3+sA s0+s5+s8+s9' s2+s6 [i]
mulx 16(up), s4, sB      | s7" s1+sB s3+sA+s4 s0+s5+s8+s9' s2+s6 [i]
movq s0, rp[i+1]         | s7" s1+sB s3+sA+s4 s5+s8+s9|' s2+s6 [i]
movq $0, s0
adox s0, s7              | s7 s1+sB s3+sA+s4 s5+s8+s9|' s2+s6 [i]
movq s3, rp[i+2]         | s7 s1+sB sA+s4| s5+s8+s9|' s2+s6 [i]
s3:=v[i+1]               | s7 s1+sB sA+s4| s5+s8+s9|' s2+s6 [i] s3=v[i+1]
adox s6, s2              | s7 s1+sB sA+s4| s5+s8+s9|'" s2 [i] s3=v[i+1]
movq s2, rp[i]           | s7 s1+sB sA+s4| s5+s8+s9|'" [i+1] s3=v[i+1]
mulx 24(up), s0, s2      | s7+s2 s1+sB+s0 sA+s4| s5+s8+s9|'" [i+1] s3=v[i+1]
adcx s8, s5              | s7+s2 s1+sB+s0 sA+s4|' s5+s9|" [i+1] s3=v[i+1]
mulx 32(up), s6, s8      | s8 s7+s2+s6 s1+sB+s0 sA+s4|' s5+s9|" [i+1] s3=v[i+1]
adox s9, s5              | s8 s7+s2+s6 s1+sB+s0 sA+s4|'" s5| [i+1] s3=v[i+1]
adcx sA, s4              | s8 s7+s2+s6 s1+sB+s0' s4|" s5| [i+1] s3=v[i+1]
movq rp[i+2], sA         | s8 s7+s2+s6 s1+sB+s0' s4+sA" s5| [i+1] s3=v[i+1]
adox sA, s4              | s8 s7+s2+s6 s1+sB+s0'" s4 s5| [i+1] s3=v[i+1]
adcx sB, s1              | s8 s7+s2+s6' s1+s0" s4 s5| [i+1] s3=v[i+1]
movq s3, dd              | s8 s7+s2+s6' s1+s0" s4 s5| [i+1]
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
data lies like that: s8 s7+s2+s6' s1+s0" s4 s5| [i] dd=v[i]
'''

g_mul_4 = '''
                         | s8 s7+s2+s6' s1+s0" s4 s5| [i]
mulx (up), s3, s9        | s8 s7+s2+s6' s1+s0" s4+s9 s5+s3| [i]
mulx 8(up), sA, sB       | s8 s7+s2+s6' s1+s0+sB" s4+s9+sA s5+s3| [i]
adcx s7, s2              | s8' s2+s6 s1+s0+sB" s4+s9+sA s5+s3| [i]
adox s1, s0              | s8' s2+s6" s0+sB s4+s9+sA s5+s3| [i]
movq $0, s7
adcx s7, s8              | s8 s2+s6" s0+sB s4+s9+sA s5+s3| [i]
mulx 16(up), s7, s1      | s8 s2+s6+s1" s0+sB+s7 s4+s9+sA s5+s3| [i]
adox s6, s2              | s8" s2+s1 s0+sB+s7 s4+s9+sA s5+s3| [i]
movq rp[i], s6           | s8" s2+s1 s0+sB+s7 s4+s9+sA s6+s5+s3 [i]
adcx s6, s5              | s8" s2+s1 s0+sB+s7 s4+s9+sA' s5+s3 [i]
movq $0, s6
adox s6, s8              | s8 s2+s1 s0+sB+s7 s4+s9+sA' s5+s3 [i]
movq up, rp[i]
mulx 24(up), up, s6      | s8+s6 s2+s1+up s0+sB+s7 s4+s9+sA' s5+s3 [i]
adcx s9, s4              | s8+s6 s2+s1+up s0+sB+s7' s4+sA s5+s3 [i]
movq rp[i], s9
adox s5, s3              | s8+s6 s2+s1+up s0+sB+s7' s4+sA" s3 [i]
movq s3, rp[i]           | s8+s6 s2+s1+up s0+sB+s7' s4+sA" [i+1]
mulx 32(s9), s3, s5      | s5 s8+s6+s3 s2+s1+up s0+sB+s7' s4+sA" [i+1]
adcx sB, s0              | s5 s8+s6+s3 s2+s1+up' s0+s7 s4+sA" [i+1]
adox sA, s4              | s5 s8+s6+s3 s2+s1+up' s0+s7" s4 [i+1]
movq s4, rp[i+1]         | s5 s8+s6+s3 s2+s1+up' s0+s7" [i+2]
movq $0, s4
adcx s2, s1              | s5 s8+s6+s3' s1+up s0+s7" [i+2] s4=0
movq s8, s2              | s5 s2+s6+s3' s1+up s0+s7" [i+2] s4=0
adox s7, s0              | s5 s2+s6+s3' s1+up" s0 [i+2] s4=0
movq s0, rp[i+2]         | s5 s2+s6+s3' s1+up" [i+3] s4=0
adcx s6, s2              | s5' s2+s3 s1+up" [i+3] s4=0
adox up, s1              | s5' s2+s3" s1 [i+3] s4=0
movq s1, rp[i+3]         | s5' s2+s3" [i+4] s4=0
adcx s4, s5              | s5 s2+s3" [i+4] s4=0
adox s3, s2              | s5" s2 [i+4] s4=0
movq s2, rp[i+4]
adox s4, s5
movq s5, rp[i+5]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_aligned as S
import gen_mul7_t03 as E
import gen_mul8_aligned as G

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
    if (i == 2):
        return 'movq t1, ' + t
    if (i == 3):
        return 'pextrq $0x1, t1, ' + t
    if (i == 4):
        return 'movq t2, ' + t

g_i_plus_patt = re.compile(r'\bi\+([0-5])')
g_v_patt = re.compile(r'(.+):=v\[([0-4])\]')
g_rp_patt = re.compile(r'rp\[(.+?)\]')
def chew_line(i, s, align):
    m = g_i_plus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (i + int(m.group(1))))
    s = re.sub(r'\bi\b', '%s' % i, s)
    
    m = g_v_patt.match(s)
    if m:
        return extract_v(int(m.group(2)), m.group(1), align)
    
    m = g_rp_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s(rp)' % (8 * int(m.group(1))))
    
    return s

def muladd_code(i, jj, p, align):
    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []
    
    for j in jj:
        k = chew_line(i, j, align)
        if k:
            rr.append(k)
    
    return [E.apply_s_permutation(j, p) for j in rr]

def alignment_code(shift):
    p = list(range(12))
    r = muladd_code(0, P.cutoff_comments(g_mul_01), p, shift)
    r += muladd_code(2, P.cutoff_comments(g_mul_2), p, shift)
    r += muladd_code(3, P.cutoff_comments(g_mul_3), p, shift)
    r += muladd_code(4, P.cutoff_comments(g_mul_4), p, shift)
    return r

def do_it(o):
    code = P.cutoff_comments(g_preamble) + alignment_code(8)
    xmm_save = P.save_registers_in_xmm(code, 9)
    P.insert_restore(code, xmm_save)
    code += ['retq', 'align0:'] + P.cutoff_comments(g_load0)
    code += alignment_code(0)

    G.save_in_xmm(code, xmm_save)
    P.insert_restore(code, xmm_save)
    S.cook_asm(o, code, xmm_save)
    
if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
