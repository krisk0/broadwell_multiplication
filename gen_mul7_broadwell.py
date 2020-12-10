'''
7x7 multiplication targeting Broadwell and Ryzen. 94 ticks on Skylake, 85 on Ryzen
'''

"""
      rdi -< rp
      rsi -< up
      rdx -< vp

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w7  w6    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w5  up  rp  dd
"""

g_var_map = 'rp,rdi up,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx t0,xmm15 t1,xmm14'

g_mul_01 = '''
movq dd, w0
!save w6
movq (dd), dd
movq w0, t0              | t0=vp
!save w7
xor w1, w1               | zero flags
mulx (up), w1, w2        | w2 w1
!save w8
mulx 8(up), w3, w4       | w4 w2+w3 w1
!save w9
mulx 16(up), w5, w6      | w6 w4+w5 w2+w3 w1
!save wA
mulx 24(up), w7, w8      | w8 w6+w7 w4+w5 w2+w3 w1
movq w1, (rp)            | w8 w6+w7 w4+w5 w2+w3 {1}
mulx 32(up), w1, w9      | w9 w8+w1 w6+w7 w4+w5 w2+w3 {1}
adcx w3, w2              | w9 w8+w1 w6+w7 w4+w5' w2 {1}
!save wB
movq 8(w0), w0           | w9 w8+w1 w6+w7 w4+w5' w2 {1} w0=v[1]
mulx 40(up), w3, wA      | wA w9+w3 w8+w1 w6+w7 w4+w5' w2 {1} w0=v[1]
movq w2, 8(rp)           | wA w9+w3 w8+w1 w6+w7 w4+w5' .. {1} w0=v[1]
mulx 48(up), wB, dd      | dd wA+wB w9+w3 w8+w1 w6+w7 w4+w5' .. {1} w0=v[1]
adcx w5, w4              | dd wA+wB w9+w3 w8+w1 w6+w7' w4 .. {1} w0=v[1]
xchg w0, dd              | w0 wA+wB w9+w3 w8+w1 w6+w7' w4 .. {1}
mulx (up), w2, w5        | w0 wA+wB w9+w3 w8+w1 w6+w7' w4+w5 w2: {1}
adcx w7, w6              | w0 wA+wB w9+w3 w8+w1' w6 w4+w5 w2: {1}
adcx w8, w1              | w0 wA+wB w9+w3' w1 w6 w4+w5 w2: {1}
mulx 8(up), w7, w8       | w0 wA+wB w9+w3' w1 w6+w8 w4+w5+w7 w2: {1}
adcx w9, w3              | w0 wA+wB' w3 w1 w6+w8 w4+w5+w7 w2: {1}
adox 8(rp), w2           | w0 wA+wB' w3 w1 w6+w8 w4+w5+w7" w2 {1}
movq w2, 8(rp)           | w0 wA+wB' w3 w1 w6+w8 w4+w5+w7" {2}
mulx 16(up), w2, w9      | w0 wA+wB' w3 w1+w9 w6+w8+w2 w4+w5+w7" {2}
adcx wB, wA              | w0' wA w3 w1+w9 w6+w8+w2 w4+w5+w7" {2}
movq $0, wB
adox w5, w4              | w0' wA w3 w1+w9 w6+w8+w2" w4+w7 {2}
adcx wB, w0              | w0 wA w3 w1+w9 w6+w8+w2" w4+w7 {2}
mulx 24(up), w5, wB      | w0 wA w3+wB w1+w9+w5 w6+w8+w2" w4+w7 {2}
adox w8, w6              | w0 wA w3+wB w1+w9+w5" w6+w2 w4+w7 {2}
movq t0, w8              | w0 wA w3+wB w1+w9+w5" w6+w2 w4+w7 {2} w8=vp
adcx w7, w4              | w0 wA w3+wB w1+w9+w5" w6+w2' w4 {2} w8=vp
adox w9, w1              | w0 wA w3+wB" w1+w5 w6+w2' w4 {2} w8=vp
mulx 32(up), w7, w9      | w0 wA+w9 w3+wB+w7" w1+w5 w6+w2' w4 {2} w8=vp
adcx w6, w2              | w0 wA+w9 w3+wB+w7" w1+w5' w2 w4 {2} w8=vp
adox wB, w3              | w0 wA+w9" w3+w7 w1+w5' w2 w4 {2} w8=vp
mulx 40(up), w6, wB      | w0+wB wA+w9+w6" w3+w7 w1+w5' w2 w4 {2} w8=vp
adcx w5, w1              | w0+wB wA+w9+w6" w3+w7' w1 w2 w4 {2} w8=vp
adox wA, w9              | w0+wB" w9+w6 w3+w7' w1 w2 w4 {2} w8=vp
movq 16(w8), w8          | w0+wB" w9+w6 w3+w7' w1 w2 w4 {2} w8=v[2]
mulx 48(up), w5, dd      | dd w0+wB+w5" w9+w6 w3+w7' w1 w2 w4 {2} w8=v[2]
movq $0, wA              | dd w0+wB+w5" w9+w6 w3+w7' w1 w2 w4 {2} w8=v[2]  wA=0
adcx w7, w3              | dd w0+wB+w5" w9+w6' w3 w1 w2 w4 {2} w8=v[2] wA=0
adox wB, w0              | dd" w0+w5 w9+w6' w3 w1 w2 w4 {2} w8=v[2] wA=0
xchg dd, w8              | w8" w0+w5 w9+w6' w3 w1 w2 w4 {2} wA=0
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that: s8" s0+s5 s9+s6' s3 s1 s2 s4 {i} sA=0  dd=v[i]
'''

g_muladd_2 = '''
                         | s8" s0+s5 s9+s6' s3 s1 s2 s4 {i} sA=0
mulx (up), s7, sB        | s8" s0+s5 s9+s6' s3 s1 s2+sB s4+s7 {i} sA=0
adcx s9, s6              | s8" s0+s5' s6 s3 s1 s2+sB s4+s7 {i} sA=0
adox sA, s8              | s8 s0+s5' s6 s3 s1 s2+sB s4+s7 {i} sA=0
adcx s5, s0              | s8' s0 s6 s3 s1 s2+sB s4+s7 {i} sA=0
mulx 8(up), s5, s9       | s8' s0 s6 s3 s1+s9 s2+sB+s5 s4+s7 {i} sA=0
adcx sA, s8              | s8 s0 s6 s3 s1+s9 s2+sB+s5 s4+s7 {i} sA=0
adox s7, s4              | s8 s0 s6 s3 s1+s9 s2+sB+s5" s4 {i} sA=0
mulx 16(up), s7, sA      | s8 s0 s6 s3+sA s1+s9+s7 s2+sB+s5" s4 {i}
adcx sB, s2              | s8 s0 s6 s3+sA s1+s9+s7' s2+s5" s4 {i}
movq s4, i(rp)           | s8 s0 s6 s3+sA s1+s9+s7' s2+s5" {i+1}
mulx 24(up), s4, sB      | s8 s0 s6+sB s3+sA+s4 s1+s9+s7' s2+s5" {i+1}
adox s5, s2              | s8 s0 s6+sB s3+sA+s4 s1+s9+s7'" s2 {i+1}
movq s2, t1
movq t0, s2
adcx s9, s1              | s8 s0 s6+sB s3+sA+s4' s1+s7" t1 {i+1} s2=vp
mulx 32(up), s5, s9      | s8 s0+s9 s6+sB+s5 s3+sA+s4' s1+s7" t1 {i+1} s2=vp
adox s7, s1              | s8 s0+s9 s6+sB+s5 s3+sA+s4'" s1 t1 {i+1} s2=vp
adcx sA, s3              | s8 s0+s9 s6+sB+s5' s3+s4" s1 t1 {i+1} s2=vp
mulx 40(up), s7, sA      | s8+sA s0+s9+s7 s6+sB+s5' s3+s4" s1 t1 {i+1} s2=vp
movq i+1(s2), s2         | s8+sA s0+s9+s7 s6+sB+s5' s3+s4" s1 t1 {i+1} s2=v[i+1]
adox s4, s3              | s8+sA s0+s9+s7 s6+sB+s5'" s3 s1 t1 {i+1} s2=v[i+1]
mulx 48(up), s4, dd      | dd s8+sA+s4 s0+s9+s7 s6+sB+s5'" s3 s1 t1 {i+1} s2=v[i+1]
adcx sB, s6              | dd s8+sA+s4 s0+s9+s7' s6+s5" s3 s1 t1 {i+1} s2=v[i+1]
movq t1, sB              | dd s8+sA+s4 s0+s9+s7' s6+s5" s3 s1 sB {i+1} s2=v[i+1]
adcx s9, s0              | dd s8+sA+s4' s0+s7 s6+s5" s3 s1 sB {i+1} s2=v[i+1]
adox s5, s6              | dd s8+sA+s4' s0+s7" s6 s3 s1 sB {i+1} s2=v[i+1]
xchg s2, dd              | s2 s8+sA+s4' s0+s7" s6 s3 s1 sB {i+1}
adcx sA, s8              | s2' s8+s4 s0+s7" s6 s3 s1 sB {i+1}
movq $0, sA              | s2' s8+s4 s0+s7" s6 s3 s1 sB {i+1}
'''

"""
old s8" s0+s5 s9+s6' s3 s1 s2 s4
now s2' s8+s4 s0+s7" s6 s3 s1 sB
"""

#         0 1 2 3 4 5 6 7 8 9 A B
g_perm = '8 3 1 6 B 4 7 5 2 0 A 9'

g_tail = '''
                         | s8 s0 s6+sB s3+sA+s4 s1+s9+s7'" s2 {i+1}
movq s2, i+1(rp)         | s8 s0 s6+sB s3+sA+s4 s1+s9+s7'" {i+2}
adcx s9, s1              | s8 s0 s6+sB s3+sA+s4' s1+s7" {i+2}
mulx 32(up), s2, s9      | s8 s0+s9 s6+sB+s2 s3+sA+s4' s1+s7" {i+2}
adox s7, s1              | s8 s0+s9 s6+sB+s2 s3+sA+s4'" s1 {i+2}
adcx sA, s3              | s8 s0+s9 s6+sB+s2' s3+s4" s1 {i+2}
mulx 40(up), s7, sA      | s8+sA s0+s9+s7 s6+sB+s2' s3+s4" s1 {i+2}
movq s1, i+2(rp)         | s8+sA s0+s9+s7 s6+sB+s2' s3+s4" {i+3}
mulx 48(up), s1, dd      | dd s8+sA+s1 s0+s9+s7 s6+sB+s2' s3+s4" {i+3}
adox s4, s3              | dd s8+sA+s1 s0+s9+s7 s6+sB+s2'" s3 {i+3}
adcx sB, s6              | dd s8+sA+s1 s0+s9+s7' s6+s2" s3 {i+3}
movq s3, i+3(rp)         | dd s8+sA+s1 s0+s9+s7' s6+s2" {i+4}
adcx s9, s0              | dd s8+sA+s1' s0+s7 s6+s2" {i+4}
adox s6, s2              | dd s8+sA+s1' s0+s7" s2 {i+4}
adcx sA, s8              | dd' s8+s1 s0+s7" s2 {i+4}
movq $0, s6              | dd' s8+s1 s0+s7" s2 {i+4} s6=0
adox s7, s0              | dd' s8+s1" s0 s2 {i+4} s6=0
movq s2, i+4(rp)         | dd' s8+s1" s0 {i+5} s6=0
adcx s6, dd              | dd s8+s1" s0 {i+5} s6=0
adox s8, s1              | dd" s1 s0 {i+5} s6=0
movq s0, i+5(rp)         | dd" s1 {i+6} s6=0
adox s6, dd              | dd s1 {i+6} s6=0
movq s1, i+6(rp)         | dd {i+7} s6=0
movq dd, i+7(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def mul1_code(i, jj, p):
    rr = ['# mul_add %s' % i] + jj

    #print post_condition(i, ' pre', '''s8" s0+s5 s9+s6' s3 s1 s2 s4''', p)

    # apply permutation p, replace i(rp)
    for y in range(len(rr)):
        src = apply_s_permutation(rr[y], p)
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i))
        rr[y] = src.rstrip()

    #print post_condition(i, 'post', '''s2' s8+s4 s0+s7" s6 s3 s1 sB''', p)

    return rr

def apply_s_permutation(c, p):
    for x in range(len(p)):
        a = '%X' % x
        b = '%X' % p[x]
        c = re.sub(r'\bs%s\b' % a, 'w' + b, c)
    return c

def post_condition(i, pre, s, p):
    s = apply_s_permutation(s, p)
    s = replace_symbolic_names_wr(s, g_var_map).replace('%', '')

    return ('%s %s-condition: ' % (i, pre)) + s

def cook_asm(o, code):
    xmm_save = P.save_registers_in_xmm(code, 9)

    P.insert_restore(code, xmm_save)
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    code = replace_symbolic_names_wr(code, g_var_map)

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

def replace_symbolic_names_wr(code, m):
    r = {}
    for x in m.split(' '):
        y = x.split(',')
        r[y[0]] = '%' + y[1]
    return P.replace_symbolic_vars_name(code, r)

def do_it(o):
    meat = P.cutoff_comments(g_mul_01)
    p = list(range(12))
    m2 = P.cutoff_comments(g_muladd_2)
    m3 = P.swap_adox_adcx(m2)
    meat += mul1_code(2, m2, p)
    q = [int(x, 16) for x in g_perm.split(' ')]
    for i in range(3, 6):
        p = P.composition(p, q)
        if i & 1:
            meat += mul1_code(i, m3, p)
        else:
            meat += mul1_code(i, m2, p)

    tail = cook_tail(m2)
    p = P.composition(p, q)
    meat += mul1_code(6, tail, p)

    cook_asm(o, meat)

def cook_tail(cc):
    rr = []
    for c in cc:
        if c.find(', t1') != -1:
            break
        rr.append(c)
    return rr + P.cutoff_comments(g_tail)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
