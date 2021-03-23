'''
10x10 multiplication targeting Zen. Uses aligned loads of v[] into xmm's.

161 ticks on Ryzen, 167 ticks on Broadwell.
'''

"""
xmm usage:
0-4 v[]
"""

g_preamble = '''
movq dd, w0
and $0xF, dd
movq w0[0], dd
jz align0
vmovdqa w0[1], x0
vmovdqa w0[3], x1
vmovdqa w0[5], x2
vmovdqa w0[7], x3
movq w0[9], x4
'''

g_load_0 = '''
align0:
movq w0[1], x0
vmovdqa w0[2], x1
vmovdqa w0[4], x2
vmovdqa w0[6], x3
vmovdqa w0[8], x4
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
mulx sp[7], w7, wA        | wA w6+w7 w8+w4 w9+w2 wB+w0' w5 [3] wC
adcx wB, w0               | wA w6+w7 w8+w4 w9+w2' w0 w5 [3] wC
mulx sp[8], w1, w3        | w3 wA+w1 w6+w7 w8+w4 w9+w2' w0 w5 [3] wC
adcx w2, w9               | w3 wA+w1 w6+w7 w8+w4' w9 w0 w5 [3] wC
mulx sp[9], w2, wB        | wB w3+w2 wA+w1 w6+w7 w8+w4' w9 w0 w5 [3] wC
movq wC, dd               | wB w3+w2 wA+w1 w6+w7 w8+w4' w9 w0 w5 [3]
adcx w4, w8               | wB w3+w2 wA+w1 w6+w7' w8 w9 w0 w5 [3]
mulx sp[0], w4, wC        | wB w3+w2 wA+w1 w6+w7' w8 w9 w0 w5 wC: w4: [1]
adcx w7, w6               | wB w3+w2 wA+w1' w6 w8 w9 w0 w5 wC: w4: [1]
movq w5, rp[3]            | wB w3+w2 wA+w1' w6 w8 w9 w0 .. wC: w4: [1]
mulx sp[1], w5, w7        | wB w3+w2 wA+w1' w6 w8 w9 w0 w7: wC+w5: w4: [1]
adcx w1, wA               | wB w3+w2' wA w6 w8 w9 w0 w7: wC+w5: w4: [1]
movq w0, rp[4]            | wB w3+w2' wA w6 w8 w9 .. w7: wC+w5: w4: [1]
mulx sp[2], w0, w1        | wB w3+w2' wA w6 w8 w9 w1: w7+w0: wC+w5: w4: [1]
adcx w2, w3               | wB' w3 wA w6 w8 w9 w1: w7+w0: wC+w5: w4: [1]
movq w6, rp[7]            | wB' w3 wA ^7 w8 w9 w1: w7+w0: wC+w5: w4: [1]
mulx sp[3], w2, w6        | wB' w3 wA ^7 w8 w9+w6 w1+w2: w7+w0: wC+w5: w4: [1]
ado2 rp[1], w4            | wB' w3 wA ^7 w8 w9+w6 w1+w2: w7+w0: wC+w5:" [2]
movq $0, w4
adcx w4, wB               | wB w3 wA ^7 w8 w9+w6 w1+w2: w7+w0: wC+w5:" [2]
ado2 rp[2], wC            | wB w3 wA ^7 w8 w9+w6 w1+w2: w7+w0:" w5: [2]
mulx sp[4], w4, wC        | wB w3 wA ^7 w8+wC w9+w6+w4 w1+w2: w7+w0:" w5: [2]
ado2 rp[3], w7            | wB w3 wA ^7 w8+wC w9+w6+w4 w1+w2:" w0: w5: [2]
adc2 rp[2], w5            | wB w3 wA ^7 w8+wC w9+w6+w4 w1+w2:" w0:' [3]
mulx sp[5], w5, w7        | wB w3 wA ^7+w7 w8+wC+w5 w9+w6+w4 w1+w2:" w0:' [3]
ado2 rp[4], w1            | wB w3 wA ^7+w7 w8+wC+w5 w9+w6+w4" w2: w0:' [3]
adc2 rp[3], w0            | wB w3 wA ^7+w7 w8+wC+w5 w9+w6+w4" w2:' [4]
mulx sp[6], w0, w1        | wB w3 wA+w1 ^7+w7+w0 w8+wC+w5 w9+w6+w4" w2:' [4]
adox w6, w9               | wB w3 wA+w1 ^7+w7+w0 w8+wC+w5" w9+w4 w2:' [4]
w6:=v[2]
adc2 rp[4], w2            | wB w3 wA+w1 ^7+w7+w0 w8+wC+w5" w9+w4' [5] w6
| delay 1 tick?
adox w8, wC               | wB w3 wA+w1 ^7+w7+w0" wC+w5 w9+w4' [5] w6
mulx sp[7], w2, w8        | wB w3+w8 wA+w1+w2 ^7+w7+w0" wC+w5 w9+w4' [5] w6
adcx w4, w9               | wB w3+w8 wA+w1+w2 ^7+w7+w0" wC+w5' w9 [5] w6
movq w9, rp[5]            | wB w3+w8 wA+w1+w2 ^7+w7+w0" wC+w5' [6] w6
mulx sp[8], w4, w9        | wB+w9 w3+w8+w4 wA+w1+w2 ^7+w7+w0" wC+w5' [6] w6
adox rp[7], w7            | wB+w9 w3+w8+w4 wA+w1+w2" w7+w0 wC+w5' [6] w6
adcx w5, wC               | wB+w9 w3+w8+w4 wA+w1+w2" w7+w0' wC [6] w6
movq wC, rp[6]            | wB+w9 w3+w8+w4 wA+w1+w2" w7+w0' [7] w6
mulx sp[9], w5, wC        | wC wB+w9+w5 w3+w8+w4 wA+w1+w2" w7+w0' [7] w6
movq w6, dd               | wC wB+w9+w5 w3+w8+w4 wA+w1+w2" w7+w0' [7]
adox w1, wA               | wC wB+w9+w5 w3+w8+w4" wA+w2 w7+w0' [7]
'''

g_mul_2 = '''
                          | i >= 2
                          | sC sB+s9+s5 s3+s8+s4" sA+s2 s7+s0' [i+5] dd=v[i]
mulx sp[0], s1, s6        | sC sB+s9+s5 s3+s8+s4" sA+s2 s7+s0' {3} s6: s1: [i]
adcx s0, s7               | sC sB+s9+s5 s3+s8+s4" sA+s2' s7 {3} s6: s1: [i]
movq s3, rp[i+5]          | sC sB+s9+s5 ^5+s8+s4" sA+s2' s7 {3} s6: s1: [i]
mulx sp[1], s0, s3        | sC sB+s9+s5 ^5+s8+s4" sA+s2' s7 {2} s3: s6+s0: s1: [i]
adox rp[i+5], s8          | sC sB+s9+s5" s8+s4 sA+s2' s7 {2} s3: s6+s0: s1: [i]
movq s7, rp[i+5]          | sC sB+s9+s5" s8+s4 sA+s2' {3} s3: s6+s0: s1: [i]
adcx s2, sA               | sC sB+s9+s5" s8+s4' sA {3} s3: s6+s0: s1: [i]
mulx sp[2], s2, s7        | sC sB+s9+s5" s8+s4' sA {2} s7: s3+s2: s6+s0: s1: [i]
adox s9, sB               | sC" sB+s5 s8+s4' sA {2} s7: s3+s2: s6+s0: s1: [i]
movq $0, s9
adcx s4, s8               | sC" sB+s5' s8 sA {2} s7: s3+s2: s6+s0: s1: [i]
adox s9, sC               | sC sB+s5' s8 sA {2} s7: s3+s2: s6+s0: s1: [i]
mulx sp[3], s4, s9        | sC sB+s5' s8 sA .. s9: s7+s4: s3+s2: s6+s0: s1: [i]
adcx s5, sB               | sC' sB s8 sA .. s9: s7+s4: s3+s2: s6+s0: s1: [i]
ado2 rp[i], s1            | sC' sB s8 sA .. s9: s7+s4: s3+s2: s6+s0:" [i+1]
mulx sp[4], s1, s5        | sC' sB s8 sA s5: s9+s1: s7+s4: s3+s2: s6+s0:" [i+1]
adox s0, s6               | sC' sB s8 sA s5: s9+s1: s7+s4: s3+s2:" s6: [i+1]
movq $0, s0
adcx s0, sC               | sC sB s8 sA s5: s9+s1: s7+s4: s3+s2:" s6: [i+1]
adox s2, s3               | sC sB s8 sA s5: s9+s1: s7+s4:" s3: s6: [i+1]
mulx sp[5], s0, s2        | sC sB s8 sA+s2 s5+s0: s9+s1: s7+s4:" s3: s6: [i+1]
adc2 rp[i+1], s6          | sC sB s8 sA+s2 s5+s0: s9+s1: s7+s4:" s3:' [i+2]
adox s4, s7               | sC sB s8 sA+s2 s5+s0: s9+s1:" s7: s3:' [i+2]
mulx sp[6], s4, s6        | sC sB s8+s6 sA+s2+s4 s5+s0: s9+s1:" s7: s3:' [i+2]
adc2 rp[i+2], s3          | sC sB s8+s6 sA+s2+s4 s5+s0: s9+s1:" s7:' [i+3]
s3:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
adox s1, s9               | sC sB s8+s6 sA+s2+s4 s5+s0:" s9: s7:' [i+3] s3
adc2 rp[i+3], s7          | sC sB s8+s6 sA+s2+s4 s5+s0:" s9:' [i+4] s3
mulx sp[7], s1, s7        | sC sB+s7 s8+s6+s1 sA+s2+s4 s5+s0:" s9:' [i+4] s3
adox s0, s5               | sC sB+s7 s8+s6+s1 sA+s2+s4" s5: s9:' [i+4] s3
adc2 rp[i+4], s9          | sC sB+s7 s8+s6+s1 sA+s2+s4" s5:' [i+5] s3
mulx sp[8], s0, s9        | sC+s9 sB+s7+s0 s8+s6+s1 sA+s2+s4" s5:' [i+5] s3
adox s2, sA               | sC+s9 sB+s7+s0 s8+s6+s1" sA+s4 s5:' [i+5] s3
adc2 rp[i+5], s5          | sC+s9 sB+s7+s0 s8+s6+s1" sA+s4' [i+6] s3
mulx sp[9], s2, s5        | s5 sC+s9+s2 sB+s7+s0 s8+s6+s1" sA+s4' [i+6] s3
movq s3, dd               | s5 sC+s9+s2 sB+s7+s0 s8+s6+s1" sA+s4' [i+6]
adox s6, s8               | s5 sC+s9+s2 sB+s7+s0" s8+s1 sA+s4' [i+6]
'''

"""
old sC sB+s9+s5 s3+s8+s4" sA+s2 s7+s0' [i+5]
new s5 sC+s9+s2 sB+s7+s0" s8+s1 sA+s4' [i+5]
          0 1 2 3 4 5 6 7 8 9 A B C"""
g_perm = '4 3 1 B 0 2 6 A 7 9 8 C 5'

g_tail = '''
| adox s1, s9             | sC sB s8+s6 sA+s2+s4 s5+s0:" s9: s7:' [i+3]
mulx sp[7], s1, s3        | sC sB+s3 s8+s6+s1 sA+s2+s4 s5+s0:" s9: s7:' [i+3]
adc2 rp[i+3], s7          | sC sB+s3 s8+s6+s1 sA+s2+s4 s5+s0:" s9:' [i+4]
adox s0, s5               | sC sB+s3 s8+s6+s1 sA+s2+s4" s5: s9:' [i+4]
mulx sp[8], s0, s7        | sC+s7 sB+s3+s0 s8+s6+s1 sA+s2+s4" s5: s9:' [i+4]
adc2 rp[i+4], s9          | sC+s7 sB+s3+s0 s8+s6+s1 sA+s2+s4" s5:' [i+5]
mulx sp[9], s9, dd        | dd sC+s7+s9 sB+s3+s0 s8+s6+s1 sA+s2+s4" s5:' [i+5]
adox s2, sA               | dd sC+s7+s9 sB+s3+s0 s8+s6+s1" sA+s4 s5:' [i+5]
adc2 rp[i+5], s5          | dd sC+s7+s9 sB+s3+s0 s8+s6+s1" sA+s4' [i+6]
adox s6, s8               | dd sC+s7+s9 sB+s3+s0" s8+s1 sA+s4' [i+6]
adcx s4, sA
movq sA, rp[i+6]          | dd sC+s7+s9 sB+s3+s0" s8+s1' [i+7]
movq rp[i+7], sp
adox s3, sB               | dd sC+s7+s9" sB+s0 s8+s1' [i+7]
adcx s1, s8
movq s8, rp[i+7]          | dd sC+s7+s9" sB+s0' [i+8]
adox s7, sC               | dd" sC+s9 sB+s0' [i+8]
movq $0, s1
adcx s0, sB               | dd" sC+s9' sB [i+8] s1
movq sB, rp[i+8]          | dd" sC+s9' [i+9] s1
adox s1, dd               | dd sC+s9' [i+9] s1
adcx s9, sC
movq sC, rp[i+9]          | dd' [i+10] s1
adcx s1, dd
movq dd, rp[i+10]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E
import gen_mul11_ryzen as C

def extract_v(i, alignment, tgt):
    if (i <= 0) or (i > 9) or (alignment == None):
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
                    'tail_jump' : (i == 8) and (alignment > 0),
                    'tail_here' : (i == 8) and (not alignment),
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
    j = ss.index('adox s1, s9') + 1
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
    for i in range(2, 9):
        code += chew_code(m2, i, alignment, p)
        p = P.composition(p, q)
    if not alignment:
        code += chew_code(tt, 9, None, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, C.g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
