'''
11x11 multiplication targeting Zen. Uses aligned loads of v[] into xmm's.

200 ticks on Ryzen, 224 ticks on Skylake.
 
TODO: Python code of gen_mul*zen.py is nearly identical
'''

"""
xmm usage:
0-5 v[]
"""

g_var_map = 'rp,rdi wC,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx sp,rsp ' + \
    ' '.join(['x%X,xmm%s' % (i, i) for i in range(16)])

g_preamble = '''
movq dd, w0
and $0xF, dd
movq w0[0], dd
jz align0
vmovdqa w0[1], x0
vmovdqa w0[3], x1
vmovdqa w0[5], x2
vmovdqa w0[7], x3
vmovdqa w0[9], x4
'''

g_load_0 = '''
align0:
movq w0[1], x0
vmovdqa w0[2], x1
vmovdqa w0[4], x2
vmovdqa w0[6], x3
vmovdqa w0[8], x4
movq w0[10], x5
'''

g_mul_01 = '''
movq sp, rp[16]
movq wC, sp
mulx sp[0], w0, w1        | w1 w0
mulx sp[1], w2, w3        | w3 w1+w2 w0
mulx sp[2], w4, w5        | w5 w3+w4 w1+w2 w0
mulx sp[3], wA, wB        | wB w5+wA w3+w4 w1+w2 w0
movq w0, rp[0]            | wB w5+wA w3+w4 w1+w2 ..
mulx sp[4], w0, w9        | w9 wB+w0 w5+wA w3+w4 w1+w2 ..
adcx w2, w1               | w9 wB+w0 w5+wA w3+w4' w1 ..
movq w1, rp[1]            | w9 wB+w0 w5+wA w3+w4' [2]
mulx sp[5], w2, w8        | w8 w9+w2 wB+w0 w5+wA w3+w4' [2]
wC:=v[1]
adcx w4, w3
movq w3, rp[2]            | w8 w9+w2 wB+w0 w5+wA' [3]
mulx sp[6], w4, w6        | w6 w8+w4 w9+w2 wB+w0 w5+wA' [3] wC
adcx wA, w5               | w6 w8+w4 w9+w2 wB+w0' w5 [3] wC
movq w5, rp[3]            | w6 w8+w4 w9+w2 wB+w0' [4] wC
mulx sp[7], w7, wA        | wA w6+w7 w8+w4 w9+w2 wB+w0' [4] wC
adcx wB, w0               | wA w6+w7 w8+w4 w9+w2' w0 [4] wC
mulx sp[8], w1, w3        | w3 wA+w1 w6+w7 w8+w4 w9+w2' w0 [4] wC
adcx w2, w9               | w3 wA+w1 w6+w7 w8+w4' w9 w0 [4] wC
mulx sp[9], w2, wB        | wB w3+w2 wA+w1 w6+w7 w8+w4' w9 w0 [4] wC
adcx w4, w8               | wB w3+w2 wA+w1 w6+w7' w8 w9 w0 [4] wC
mulx sp[10], w4, w5       | w5 wB+w4 w3+w2 wA+w1 w6+w7' w8 w9 w0 [4] wC
movq wC, dd
adcx w7, w6               | w5 wB+w4 w3+w2 wA+w1' w6 w8 w9 w0 [4]
mulx sp[0], w7, wC        | w5 wB+w4 w3+w2 wA+w1' w6 w8 w9 w0 .. wC: w7: [1]
adcx w1, wA               | w5 wB+w4 w3+w2' wA w6 w8 w9 w0 .. wC: w7: [1]
movq wA, rp[4]            | w5 wB+w4 w3+w2' ^4 w6 w8 w9 w0 .. wC: w7: [1]
mulx sp[1], w1, wA        | w5 wB+w4 w3+w2' ^4 w6 w8 w9 w0 wA: wC+w1: w7: [1]
adcx w2, w3               | w5 wB+w4' w3 ^4 w6 w8 w9 w0 wA: wC+w1: w7: [1]
movq w3, rp[5]            | w5 wB+w4' ^5 ^4 w6 w8 w9 w0 wA: wC+w1: w7: [1]
mulx sp[2], w2, w3        | w5 wB+w4' ^5 ^4 w6 w8 w9 w0+w3 wA+w2: wC+w1: w7: [1]
adcx w4, wB               | w5' wB ^5 ^4 w6 w8 w9 w0+w3 wA+w2: wC+w1: w7: [1]
movq wB, rp[6]            | w5' ^6 ^5 ^4 w6 w8 w9 w0+w3 wA+w2: wC+w1: w7: [1]
mulx sp[3], w4, wB        | w5' ^6 ^5 ^4 w6 w8 w9+wB w0+w3+w4 wA+w2: wC+w1: w7: [1]
ado2 rp[1], w7            | w5' ^6 ^5 ^4 w6 w8 w9+wB w0+w3+w4 wA+w2: wC+w1:" [2]
movq $0, w7
adcx w7, w5               | w5 ^6 ^5 ^4 w6 w8 w9+wB w0+w3+w4 wA+w2: wC+w1:" [2]
ado2 rp[2], wC            | w5 ^6 ^5 ^4 w6 w8 w9+wB w0+w3+w4 wA+w2:" w1: [2]
mulx sp[4], w7, wC        | w5 ^6 ^5 ^4 w6 w8+wC w9+wB+w7 w0+w3+w4 wA+w2:" w1: [2]
ado2 rp[3], wA            | w5 ^6 ^5 ^4 w6 w8+wC w9+wB+w7 w0+w3+w4" w2: w1: [2]
adc2 rp[2], w1            | w5 ^6 ^5 ^4 w6 w8+wC w9+wB+w7 w0+w3+w4" w2:' [3]
mulx sp[5], w1, wA        | w5 ^6 ^5 ^4 w6+wA w8+wC+w1 w9+wB+w7 w0+w3+w4" w2:' [3]
adox w3, w0               | w5 ^6 ^5 ^4 w6+wA w8+wC+w1 w9+wB+w7" w0+w4 w2:' [3]
adc2 rp[3], w2            | w5 ^6 ^5 ^4 w6+wA w8+wC+w1 w9+wB+w7" w0+w4' [4]
mulx sp[6], w3, w2        | w5 ^6 ^5 ^4+w2 w6+wA+w3 w8+wC+w1 w9+wB+w7" w0+w4' [4]
adox wB, w9               | w5 ^6 ^5 ^4+w2 w6+wA+w3 w8+wC+w1" w9+w7 w0+w4' [4]
movq rp[4], wB            | w5 ^6 ^5 wB+w2 w6+wA+w3 w8+wC+w1" w9+w7 w0+w4' [4]
adcx w4, w0               | w5 ^6 ^5 wB+w2 w6+wA+w3 w8+wC+w1" w9+w7' w0 [4]
movq w0, rp[4]            | w5 ^6 ^5 wB+w2 w6+wA+w3 w8+wC+w1" w9+w7' [5]
mulx sp[7], w0, w4        | w5 ^6 ^5+w4 wB+w2+w0 w6+wA+w3 w8+wC+w1" w9+w7' [5]
adox wC, w8               | w5 ^6 ^5+w4 wB+w2+w0 w6+wA+w3" w8+w1 w9+w7' [5]
movq rp[5], wC            | w5 ^6 wC+w4 wB+w2+w0 w6+wA+w3" w8+w1 w9+w7' [5]
adcx w7, w9               | w5 ^6 wC+w4 wB+w2+w0 w6+wA+w3" w8+w1' w9 [5]
movq w9, rp[5]            | w5 ^6 wC+w4 wB+w2+w0 w6+wA+w3" w8+w1' [6]
w7:=v[2]
movq w5, rp[7]            | ^7 ^6 wC+w4 wB+w2+w0 w6+wA+w3" w8+w1' [6] w7
mulx sp[8], w5, w9        | ^7 ^6+w9 wC+w4+w5 wB+w2+w0 w6+wA+w3" w8+w1' [6] w7
adox wA, w6               | ^7 ^6+w9 wC+w4+w5 wB+w2+w0" w6+w3 w8+w1' [6] w7
movq rp[6], wA            | ^7 wA+w9 wC+w4+w5 wB+w2+w0" w6+w3 w8+w1' [6] w7
adcx w1, w8               | ^7 wA+w9 wC+w4+w5 wB+w2+w0" w6+w3' w8 [6] w7
movq w8, rp[6]            | ^7 wA+w9 wC+w4+w5 wB+w2+w0" w6+w3' [7] w7
mulx sp[9], w1, w8        | ^7+w8 wA+w9+w1 wC+w4+w5 wB+w2+w0" w6+w3' [7] w7
adox w2, wB               | ^7+w8 wA+w9+w1 wC+w4+w5" wB+w0 w6+w3' [7] w7
adcx w3, w6               | ^7+w8 wA+w9+w1 wC+w4+w5" wB+w0' w6 [7] w7
mulx sp[10], w2, w3       | w3 ^7+w8+w2 wA+w9+w1 wC+w4+w5" wB+w0' w6 [7] w7
movq w7, dd
movq rp[7], w7            | w3 w7+w8+w2 wA+w9+w1 wC+w4+w5" wB+w0' w6 [7]
adox w4, wC               | w3 w7+w8+w2 wA+w9+w1" wC+w5 wB+w0' w6 [7]
adcx w0, wB               | w3 w7+w8+w2 wA+w9+w1" wC+w5' wB w6 [7]
'''

g_mul_2 = '''
                          | i >= 2
                          | s3 s7+s8+s2 sA+s9+s1" sC+s5' sB s6 [i+5] dd=v[i]
mulx sp[0], s0, s4        | s3 s7+s8+s2 sA+s9+s1" sC+s5' sB s6 {3} s4: s0: [i]
adox s9, sA               | s3 s7+s8+s2" sA+s1 sC+s5' sB s6 {3} s4: s0: [i]
adcx s5, sC               | s3 s7+s8+s2" sA+s1' sC sB s6 {3} s4: s0: [i]
mulx sp[1], s5, s9        | s3 s7+s8+s2" sA+s1' sC sB s6 {2} s9: s4+s5: s0: [i]
adox s8, s7               | s3" s7+s2 sA+s1' sC sB s6 {2} s9: s4+s5: s0: [i]
adcx s1, sA               | s3" s7+s2' sA sC sB s6 {2} s9: s4+s5: s0: [i]
movq sA, rp[i+5]          | s3" s7+s2' ^5 sC sB s6 {2} s9: s4+s5: s0: [i]
movq $0, sA
mulx sp[2], s1, s8        | s3" s7+s2' ^5 sC sB s6 .. s8: s9+s1: s4+s5: s0: [i]
adox sA, s3               | s3 s7+s2' ^5 sC sB s6 .. s8: s9+s1: s4+s5: s0: [i]
adcx s2, s7               | s3' s7 ^5 sC sB s6 .. s8: s9+s1: s4+s5: s0: [i]
mulx sp[3], s2, sA        | s3' s7 ^5 sC sB s6 sA: s8+s2: s9+s1: s4+s5: s0: [i]
ado2 rp[i], s0            | s3' s7 ^5 sC sB s6 sA: s8+s2: s9+s1: s4+s5:" [i+1]
movq $0, s0
adcx s0, s3               | s3 s7 ^5 sC sB s6 sA: s8+s2: s9+s1: s4+s5:" [i+1]
ado2 rp[i+1], s4          | s3 s7 ^5 sC sB s6 sA: s8+s2: s9+s1:" s5: [i+1]
mulx sp[4], s0, s4        | s3 s7 ^5 sC sB s6+s4 sA+s0: s8+s2: s9+s1:" s5: [i+1]
ado2 rp[i+2], s9          | s3 s7 ^5 sC sB s6+s4 sA+s0: s8+s2:" s1: s5: [i+1]
adc2 rp[i+1], s5          | s3 s7 ^5 sC sB s6+s4 sA+s0: s8+s2:" s1:' [i+2]
mulx sp[5], s5, s9        | s3 s7 ^5 sC sB+s9 s6+s4+s5 sA+s0: s8+s2:" s1:' [i+2]
ado2 rp[i+3], s8          | s3 s7 ^5 sC sB+s9 s6+s4+s5 sA+s0:" s2: s1:' [i+2]
adc2 rp[i+2], s1          | s3 s7 ^5 sC sB+s9 s6+s4+s5 sA+s0:" s2:' [i+3]
mulx sp[6], s1, s8        | s3 s7 ^5 sC+s8 sB+s9+s1 s6+s4+s5 sA+s0:" s2:' [i+3]
ado2 rp[i+4], sA          | s3 s7 ^5 sC+s8 sB+s9+s1 s6+s4+s5" s0: s2:' [i+3]
adc2 rp[i+3], s2          | s3 s7 ^5 sC+s8 sB+s9+s1 s6+s4+s5" s0:' [i+4]
mulx sp[7], s2, sA        | s3 s7 ^5+sA sC+s8+s2 sB+s9+s1 s6+s4+s5" s0:' [i+4]
adox s4, s6               | s3 s7 ^5+sA sC+s8+s2 sB+s9+s1" s6+s5 s0:' [i+4]
s4:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
adc2 rp[i+4], s0          | s3 s7 ^5+sA sC+s8+s2 sB+s9+s1" s6+s5' [i+5] s4
movq s3, rp[i+6]          | ^6 s7 ^5+sA sC+s8+s2 sB+s9+s1" s6+s5' [i+5] s4
mulx sp[8], s0, s3        | ^6 s7+s3 ^5+sA+s0 sC+s8+s2 sB+s9+s1" s6+s5' [i+5] s4
adox s9, sB               | ^6 s7+s3 ^5+sA+s0 sC+s8+s2" sB+s1 s6+s5' [i+5] s4
movq rp[i+5], s9          | ^6 s7+s3 s9+sA+s0 sC+s8+s2" sB+s1 s6+s5' [i+5] s4
adcx s5, s6               | ^6 s7+s3 s9+sA+s0 sC+s8+s2" sB+s1' s6 [i+5] s4
movq s6, rp[i+5]          | ^6 s7+s3 s9+sA+s0 sC+s8+s2" sB+s1' [i+6] s4
mulx sp[9], s5, s6        | ^6+s6 s7+s3+s5 s9+sA+s0 sC+s8+s2" sB+s1' [i+6] s4
adox s8, sC               | ^6+s6 s7+s3+s5 s9+sA+s0" sC+s2 sB+s1' [i+6] s4
adcx s1, sB               | ^6+s6 s7+s3+s5 s9+sA+s0" sC+s2' sB [i+6] s4
mulx sp[10], s1, s8       | s8 ^6+s6+s1 s7+s3+s5 s9+sA+s0" sC+s2' sB [i+6] s4
movq s4, dd
movq rp[i+6], s4          | s8 s4+s6+s1 s7+s3+s5 s9+sA+s0" sC+s2' sB [i+6]
adox sA, s9               | s8 s4+s6+s1 s7+s3+s5" s9+s0 sC+s2' sB [i+6]
adcx s2, sC               | s8 s4+s6+s1 s7+s3+s5" s9+s0' sC sB [i+6]
'''

"""
old s3 s7+s8+s2 sA+s9+s1" sC+s5' sB s6 [i+5]
new s8 s4+s6+s1 s7+s3+s5" s9+s0' sC sB [i+5]
          0 1 2 3 4 5 6 7 8 9 A B C"""
g_perm = '2 5 1 8 A 0 B 4 6 3 7 C 9'

g_tail = '''
| adc2 rp[i+4], s0        | s3 s7 ^5+sA sC+s8+s2 sB+s9+s1" s6+s5' [i+5]
mulx sp[8], s0, s4        | s3 s7+s4 ^5+sA+s0 sC+s8+s2 sB+s9+s1" s6+s5' [i+5]
adox s9, sB               | s3 s7+s4 ^5+sA+s0 sC+s8+s2" sB+s1 s6+s5' [i+5]
movq rp[i+5], s9          | s3 s7+s4 s9+sA+s0 sC+s8+s2" sB+s1 s6+s5' [i+5]
adcx s5, s6               | s3 s7+s4 s9+sA+s0 sC+s8+s2" sB+s1' s6 [i+5]
movq s6, rp[i+5]          | s3 s7+s4 s9+sA+s0 sC+s8+s2" sB+s1' [i+6]
mulx sp[9], s5, s6        | s3+s6 s7+s4+s5 s9+sA+s0 sC+s8+s2" sB+s1' [i+6]
adox s8, sC               | s3+s6 s7+s4+s5 s9+sA+s0" sC+s2 sB+s1' [i+6]
mulx sp[10], s8, dd       | dd s3+s6+s8 s7+s4+s5 s9+sA+s0" sC+s2 sB+s1' [i+6]
movq rp[i+6], sp
adcx s1, sB               | dd s3+s6+s8 s7+s4+s5 s9+sA+s0" sC+s2' sB [i+6]
movq sB, rp[i+6]          | dd s3+s6+s8 s7+s4+s5 s9+sA+s0" sC+s2' [i+7]
adox sA, s9               | dd s3+s6+s8 s7+s4+s5" s9+s0 sC+s2' [i+7]
adcx s2, sC               | dd s3+s6+s8 s7+s4+s5" s9+s0' sC [i+7]
movq sC, rp[i+7]          | dd s3+s6+s8 s7+s4+s5" s9+s0' [i+8]
adox s4, s7               | dd s3+s6+s8" s7+s5 s9+s0' [i+8]
adcx s0, s9               | dd s3+s6+s8" s7+s5' s9 [i+8]
movq s9, rp[i+8]          | dd s3+s6+s8" s7+s5' [i+9]
movq $0, s0
adox s6, s3               | dd" s3+s8 s7+s5' [i+9]
adcx s5, s7
movq s7, rp[i+9]          | dd" s3+s8' [i+10]
adox s0, dd               | dd s3+s8' [i+10]
adcx s8, s3
movq s3, rp[i+10]         | dd' [i+11]
adcx s0, dd
movq dd, rp[i+11]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E

def extract_v(i, alignment, tgt):
    if (i <= 0) or (i > 10) or (alignment == None):
        return
    if alignment:
        i -= 1
        # 0,1 -> x0,    2,3 -> x1
        if i & 1:
            return 'pextrq $0x1, x%s, %s' % (i / 2, tgt)
        else:
            return 'movq x%s, %s' % (i / 2, tgt)
    if i == 1:
        return 'movq x0, ' + tgt
    i -= 2          # 0,1 -> x1,    2,3 -> x2
    j = i / 2 + 1
    if i & 1:
        return 'pextrq $0x1, x%s, %s' % (j, tgt)
    else:
        return 'movq x%s, %s' % (j, tgt)

g_array_patt = re.compile(r'\b([a-zA-Z0-9]+)\b\[(.+?)\]')
g_v_patt = re.compile(r'(.+):=v\[(.+)\]')
g_iplus_patt = re.compile(r'i\+(.+?)\b')
g_if_patt = re.compile(r'if (.+): (.+)')
g_ad2_patt = re.compile(r'(ad[co])2 (.+), (.+)')
def evaluate_row(s, i, alignment):
    m = g_if_patt.match(s)
    if m:
        d = \
                {\
                    'tail_jump' : (i == 9) and (alignment > 0),
                    'tail_here' : (i == 9) and (not alignment),
                }
        s = P.evaluate_if(s, d, m.group(1), m.group(2))

    m = g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
    s = re.sub(r'\bi\b', '%s' % i, s)

    m = g_v_patt.match(s)
    if m:
        return [extract_v(int(m.group(2)), alignment, m.group(1))]

    m = g_array_patt.search(s)
    if m:
        j = int(m.group(2))
        if j == 0:
            s = s.replace(m.group(), '(%s)' % m.group(1))
        else:
            s = s.replace(m.group(), '%s(%s)' % (j * 8, m.group(1)))

    m = g_ad2_patt.match(s)
    if m:
        return \
                [
                    '%sx %s, %s' % (m.group(1), m.group(2), m.group(3)),
                    'movq %s, %s' % (m.group(3), m.group(2))
                ]

    return [s]

def chew_code(src, i, aligned, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in src:
        for k in evaluate_row(j, i, aligned):
            if k:
                rr.append(k)
                if k == 'jmp tail':
                    break

    if not p:
        return rr
    re = []
    for x in rr:
        if x[0] == '#':
            re.append(x)
        else:
            re.append(E.apply_s_permutation(x, p))
    return re

def form_tail(ss):
    j = ss.index('adc2 rp[i+4], s0') + 1
    return ss[:j] + P.cutoff_comments(g_tail)

def alignment_code(alignment):
    if alignment:
        code = chew_code(g_preamble, 0, None, None)
    else:
        code = chew_code(g_load_0, None, True, None)

    code += chew_code(g_mul_01, 0, alignment, None)
    m2 = P.cutoff_comments(g_mul_2)
    tt = form_tail(m2)
    p = list(range(0xC + 1))
    q = [int(i, 16) for i in g_perm.split(' ')]
    for i in range(2, 10):
        code += chew_code(m2, i, alignment, p)
        p = P.composition(p, q)
    if not alignment:
        code += chew_code(tt, 10, None, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
