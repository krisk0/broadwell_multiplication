'''
9x9 multiplication targeting Ryzen. Uses aligned loads of v[] into xmm's.

126 ticks on Ryzen, 137 on Skylake.
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
movdqa w0[1], x0
movdqa w0[3], x1
movdqa w0[5], x2
movdqa w0[7], x3
'''

g_load_0 = '''
align0:
movq w0[1], x0
movdqa w0[2], x1
movdqa w0[4], x2
movdqa w0[6], x3
movq w0[8], x4
'''

g_mul_01 = '''
movq sp, rp[13]
movq wC, sp
| TODO: try wC (sp) instead of sp (wC)
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
mulx sp[6], w4, w6        | w6 w8+w4 w9+w2 wB+w0 w5+wA' [3] w1
adcx wA, w5               | w6 w8+w4 w9+w2 wB+w0' w5 [3] w1
mulx sp[7], w7, wA        | wA w6+w7 w8+w4 w9+w2 wB+w0' w5 [3] w1
adcx wB, w0               | wA w6+w7 w8+w4 w9+w2' w0 w5 [3] w1
mulx sp[8], w1, w3        | w3 wA+w1 w6+w7 w8+w4 w9+w2' w0 w5 [3] w1
movq wC, dd               | w3 wA+w1 w6+w7 w8+w4 w9+w2' w0 w5 [3]
adcx w2, w9               | w3 wA+w1 w6+w7 w8+w4' w9 w0 w5 [3]
mulx sp[0], wB, wC        | w3 wA+w1 w6+w7 w8+w4' w9 w0 w5 wC: wB: [1]
adcx w4, w8               | w3 wA+w1 w6+w7' w8 w9 w0 w5 wC: wB: [1]
mulx sp[1], w2, w4        | w3 wA+w1 w6+w7' w8 w9 w0 w5+w4 wC+w2: wB: [1]
adcx w7, w6               | w3 wA+w1' w6 w8 w9 w0 w5+w4 wC+w2: wB: [1]
movq w5, rp[3]            | w3 wA+w1' w6 w8 w9 w0 w4: wC+w2: wB: [1]
mulx sp[2], w5, w7        | w3 wA+w1' w6 w8 w9 w0+w7 w4+w5: wC+w2: wB: [1]
adcx w1, wA               | w3' wA w6 w8 w9 w0+w7 w4+w5: wC+w2: wB: [1]
movq wA, rp[4]            | w3' ^4 w6 w8 w9 w0+w7 w4+w5: wC+w2: wB: [1]
mulx sp[3], w1, wA        | w3' ^4 w6 w8 w9+wA w0+w7+w1 w4+w5: wC+w2: wB: [1]
ado2 rp[1], wB            | w3' ^4 w6 w8 w9+wA w0+w7+w1 w4+w5: wC+w2:" [2]
movq $0, wB
adcx wB, w3               | w3 ^4 w6 w8 w9+wA w0+w7+w1 w4+w5: wC+w2:" [2]
movq w3, rp[5]            | ^5 ^4 w6 w8 w9+wA w0+w7+w1 w4+w5: wC+w2:" [2]
mulx sp[4], w3, wB        | ^5 ^4 w6 w8+wB w9+wA+w3 w0+w7+w1 w4+w5: wC+w2:" [2]
adox w2, wC               | ^5 ^4 w6 w8+wB w9+wA+w3 w0+w7+w1 w4+w5:" wC: [2]
movq w6, rp[6]            | ^5 ^4 ^6 w8+wB w9+wA+w3 w0+w7+w1 w4+w5:" wC: [2]
mulx sp[5], w2, w6        | ^5 ^4 ^6+w6 w8+wB+w2 w9+wA+w3 w0+w7+w1 w4+w5:" wC: [2]
ado2 rp[3], w4            | ^5 ^4 ^6+w6 w8+wB+w2 w9+wA+w3 w0+w7+w1" w5: wC: [2]
w4:=v[2]
adc2 rp[2], wC            | ^5 ^4 ^6+w6 w8+wB+w2 w9+wA+w3 w0+w7+w1" w5:' [3] w4
adox w7, w0               | ^5 ^4 ^6+w6 w8+wB+w2 w9+wA+w3" w0+w1 w5:' [3] w4
mulx sp[6], w7, wC        | ^5 ^4+wC ^6+w6+w7 w8+wB+w2 w9+wA+w3" w0+w1 w5:' [3] w4
adc2 rp[3], w5            | ^5 ^4+wC ^6+w6+w7 w8+wB+w2 w9+wA+w3" w0+w1' [4] w4
adox wA, w9               | ^5 ^4+wC ^6+w6+w7 w8+wB+w2" w9+w3 w0+w1' [4] w4
mulx sp[7], w5, wA        | ^5+wA ^4+wC+w5 ^6+w6+w7 w8+wB+w2" w9+w3 w0+w1' [4] w4
adcx w1, w0               | ^5+wA ^4+wC+w5 ^6+w6+w7 w8+wB+w2" w9+w3' w0 [4] w4
movq rp[4], w1            | ^5+wA w1+wC+w5 ^6+w6+w7 w8+wB+w2" w9+w3' w0 [4] w4
movq w0, rp[4]            | ^5+wA w1+wC+w5 ^6+w6+w7 w8+wB+w2" w9+w3' [5] w4
adox wB, w8               | ^5+wA w1+wC+w5 ^6+w6+w7" w8+w2 w9+w3' [5] w4
mulx sp[8], w0, wB        | wB ^5+wA+w0 w1+wC+w5 ^6+w6+w7" w8+w2 w9+w3' [5] w4
movq w4, dd
adcx w3, w9               | wB ^5+wA+w0 w1+wC+w5 ^6+w6+w7" w8+w2' w9 [5]
adox rp[6], w6            | wB ^5+wA+w0 w1+wC+w5" w6+w7 w8+w2' w9 [5]
'''

g_mul_2 = '''
                          | i >= 2
                          | sB ^3+sA+s0 s1+sC+s5" s6+s7 s8+s2' s9 [i+3] dd=v[i]
mulx sp[0], s3, s4        | sB ^3+sA+s0 s1+sC+s5" s6+s7 s8+s2' s9 .. s4: s3: [i]
adcx s2, s8               | sB ^3+sA+s0 s1+sC+s5" s6+s7' s8 s9 .. s4: s3: [i]
adox sC, s1               | sB ^3+sA+s0" s1+s5 s6+s7' s8 s9 .. s4: s3: [i]
mulx sp[1], s2, sC        | sB ^3+sA+s0" s1+s5 s6+s7' s8 s9 sC: s4+s2: s3: [i]
adcx s7, s6               | sB ^3+sA+s0" s1+s5' s6 s8 s9 sC: s4+s2: s3: [i]
adox rp[i+3], sA          | sB" sA+s0 s1+s5' s6 s8 s9 sC: s4+s2: s3: [i]
movq s9, rp[i+3]          | sB" sA+s0 s1+s5' s6 s8 .. sC: s4+s2: s3: [i]
mulx sp[2], s7, s9        | sB" sA+s0 s1+s5' s6 s8 s9: sC+s7: s4+s2: s3: [i]
adcx s5, s1               | sB" sA+s0' s1 s6 s8 s9: sC+s7: s4+s2: s3: [i]
movq $0, s5
adox s5, sB               | sB sA+s0' s1 s6 s8 s9: sC+s7: s4+s2: s3: [i]
adcx s0, sA               | sB' sA s1 s6 s8 s9: sC+s7: s4+s2: s3: [i]
mulx sp[3], s0, s5        | sB' sA s1 s6 s8+s5 s9+s0: sC+s7: s4+s2: s3: [i]
ado2 rp[i], s3            | sB' sA s1 s6 s8+s5 s9+s0: sC+s7: s4+s2:" [i+1]
movq $0, s3
adcx s3, sB               | sB sA s1 s6 s8+s5 s9+s0: sC+s7: s4+s2:" [i+1]
adox s2, s4               | sB sA s1 s6 s8+s5 s9+s0: sC+s7:" s4: [i+1]
mulx sp[4], s2, s3        | sB sA s1 s6+s3 s8+s5+s2 s9+s0: sC+s7:" s4: [i+1]
adox s7, sC               | sB sA s1 s6+s3 s8+s5+s2 s9+s0:" sC: s4: [i+1]
adc2 rp[i+1], s4          | sB sA s1 s6+s3 s8+s5+s2 s9+s0:" sC:' [i+2]
mulx sp[5], s4, s7        | sB sA s1+s7 s6+s3+s4 s8+s5+s2 s9+s0:" sC:' [i+2]
adox s0, s9               | sB sA s1+s7 s6+s3+s4 s8+s5+s2" s9: sC:' [i+2]
s0:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
adc2 rp[i+2], sC          | sB sA s1+s7 s6+s3+s4 s8+s5+s2" s9:' [i+3] s0
movq sB, rp[i+4]          | ^4 sA s1+s7 s6+s3+s4 s8+s5+s2" s9:' [i+3] s0
mulx sp[6], sB, sC        | ^4 sA+sC s1+s7+sB s6+s3+s4 s8+s5+s2" s9:' [i+3] s0
adox s5, s8               | ^4 sA+sC s1+s7+sB s6+s3+s4" s8+s2 s9:' [i+3] s0
adc2 rp[i+3], s9          | ^4 sA+sC s1+s7+sB s6+s3+s4" s8+s2' [i+4] s0
mulx sp[7], s5, s9        | ^4+s9 sA+sC+s5 s1+s7+sB s6+s3+s4" s8+s2' [i+4] s0
adox s3, s6               | ^4+s9 sA+sC+s5 s1+s7+sB" s6+s4 s8+s2' [i+4] s0
adcx s2, s8               | ^4+s9 sA+sC+s5 s1+s7+sB" s6+s4' s8 [i+4] s0
mulx sp[8], s2, s3        | s3 ^4+s9+s2 sA+sC+s5 s1+s7+sB" s6+s4' s8 [i+4] s0
movq s0, dd               | s3 ^4+s9+s2 sA+sC+s5 s1+s7+sB" s6+s4' s8 [i+4]
adox s7, s1               | s3 ^4+s9+s2 sA+sC+s5" s1+sB s6+s4' s8 [i+4]
'''

"""
old sB ^3+sA+s0 s1+sC+s5" s6+s7 s8+s2' s9 [i+3]
new s3 ^3+s9+s2 sA+sC+s5" s1+sB s6+s4' s8 [i+3]
          0 1 2 3 4 5 6 7 8 9 A B C"""
g_perm = '2 A 4 0 7 5 1 B 6 8 9 3 C'

g_tail = '''
                          | sB sA s1+s7 s6+s3+s4 s8+s5+s2" s9:' [i+3]
mulx sp[6], s0, sC        | sB sA+sC s1+s7+s0 s6+s3+s4 s8+s5+s2" s9:' [i+3]
adox s5, s8               | sB sA+sC s1+s7+s0 s6+s3+s4" s8+s2 s9:' [i+3]
adc2 rp[i+3], s9          | sB sA+sC s1+s7+s0 s6+s3+s4" s8+s2' [i+4]
mulx sp[7], s5, s9        | sB+s9 sA+sC+s5 s1+s7+s0 s6+s3+s4" s8+s2' [i+4]
adox s3, s6               | sB+s9 sA+sC+s5 s1+s7+s0" s6+s4 s8+s2' [i+4]
adcx s2, s8
movq s8, rp[i+4]          | sB+s9 sA+sC+s5 s1+s7+s0" s6+s4' [i+5]
mulx sp[8], s2, s3        | s3 sB+s9+s2 sA+sC+s5 s1+s7+s0" s6+s4' [i+5]
movq rp[i+5], sp
adox s7, s1               | s3 sB+s9+s2 sA+sC+s5" s1+s0 s6+s4' [i+5]
adcx s4, s6
movq s6, rp[i+5]          | s3 sB+s9+s2 sA+sC+s5" s1+s0' [i+6]
| delay 1 tick?
adox sC, sA               | s3 sB+s9+s2" sA+s5 s1+s0' [i+6]
adcx s0, s1               | s3 sB+s9+s2" sA+s5' s1 [i+6]
movq s1, rp[i+6]          | s3 sB+s9+s2" sA+s5' [i+7]
adox s9, sB               | s3" sB+s2 sA+s5' [i+7]
movq $0, s0
adcx s5, sA               | s3" sB+s2' sA [i+7]
movq sA, rp[i+7]          | s3" sB+s2' [i+8]
adox s0, s3               | s3 sB+s2' [i+8]
adcx s2, sB               | s3' sB [i+8]
movq sB, rp[i+8]
adcx s0, s3
movq s3, rp[i+9]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E
import gen_mul11_ryzen as C

def extract_v(i, alignment, tgt):
    if (i <= 0) or (i > 8) or (alignment == None):
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
                    'tail_jump' : (i == 7) and (alignment > 0),
                    'tail_here' : (i == 7) and (not alignment),
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
    j = ss.index('adc2 rp[i+2], sC') + 1
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
    for i in range(2, 8):
        code += chew_code(m2, i, alignment, p)
        p = P.composition(p, q)
    if not alignment:
        code += chew_code(tt, 8, None, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, C.g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
